# APP/LOGICAL/TASKS/RESCHEDULE.PY

# ## PYTHON IMPORTS
import os
import time
import random
import datetime

# ## PACKAGE IMPORTS
from utility.time import time_ago, seconds_from_now_local, process_utc_timestring, local_timezone
from utility.uprint import buffered_print, print_warning, print_error

# ## LOCAL IMPORTS
from ... import SCHEDULER, SESSION
from ..logger import log_error
from ..network import prebooru_json_request
from ..database.server_info_db import get_last_activity
from ..database.jobs_db import get_all_job_info, get_all_job_items, update_job_item, update_job_by_id
from . import JOB_CONFIG


# ## GLOBAL VARIABLES

LAST_CHECK = time.time()


# ## FUNCTIONS

# #### Main functions

def recheck_schedule_interval(reschedule):
    global LAST_CHECK
    printer = buffered_print("Recheck Schedule Interval", header=False)
    printer("PID:", os.getpid())
    printer("Local time:", datetime.datetime.now().ctime())
    user_activity = get_last_activity('user')
    server_activity = get_last_activity('server')
    printer("User last activity:", time_ago(user_activity) if user_activity is not None else None)
    printer("Server last activity:", time_ago(server_activity) if server_activity is not None else None)
    info = get_all_job_info()
    locks = get_all_job_items('job_lock')
    manual = get_all_job_items('job_manual')
    timevals = get_all_job_items('job_time')
    if reschedule:
        orig_info = info.copy()
        _check_timeout(info, timevals, printer)
        _deconflict_tasks(info, printer)
        _unlock_tasks(info, locks, manual, printer)
        change_info = {}
        for id in orig_info:
            if orig_info[id] != info[id]:
                change_info[id] = info[id]
    else:
        change_info = {}
    _print_tasks(info, printer)
    LAST_CHECK = time.time()
    printer.print()
    SESSION.commit()
    SESSION.remove()
    # Save modifying the scheduler to last, to avoid committing early and causing a file deadlock
    for id in change_info:
        SCHEDULER.modify_job(id, 'default', next_run_time=change_info[id].replace(tzinfo=local_timezone()))


def reschedule_task(id, reschedule_soon):
    if reschedule_soon:
        next_run_time = _reschedule_soon_runtime(id)
    else:
        time_config = {k: v
                       for (k, v) in JOB_CONFIG[id]['config'].items()
                       if k in ['seconds', 'minutes', 'hours', 'days', 'weeks']}
        next_run_time = datetime.datetime.now() + datetime.timedelta(**time_config)
    update_job_by_id('job_time', id, {'time': next_run_time.timestamp()})
    SESSION.commit()
    SESSION.remove()
    SCHEDULER.modify_job(id, 'default', next_run_time=next_run_time.replace(tzinfo=local_timezone()))


def reschedule_from_child(id):
    """A child does not have access to the scheduler, so it must notify the parent."""
    next_run_time = _reschedule_soon_runtime(id)
    data = {
        'next_run_time': next_run_time.replace(tzinfo=local_timezone()).isoformat(timespec='seconds')
    }
    result = prebooru_json_request(f'/jobs/{id}', 'put', json=data)
    if not isinstance(result, dict):
        print_error(f'reschedule_from_child-{id}', result)
        log_error('tasks.initialize.reschedule_from_child', f"Error rescheduling {id}:\n" + str(result))
    elif result.get('id') != id or process_utc_timestring(result.get('next_run_time')) != next_run_time:
        print_warning(f'reschedule_from_child-{id}', next_run_time, result)


def schedule_from_child(id, func, args, next_run_time):
    """A child does not have access to the scheduler, so it must notify the parent."""
    data = {
        'id': id,
        'func': func,
        'args': [args],
        'next_run_time': next_run_time.replace(tzinfo=local_timezone()).isoformat(timespec='seconds')
    }
    result = prebooru_json_request('/jobs', 'post', json=data)
    if not isinstance(result, dict):
        print_error(f'reschedule_from_child-{id}', result)
        log_error('tasks.initialize.schedule_from_child', f"Error rescheduling {id}:\n" + str(result))
    elif result.get('id') != id or process_utc_timestring(result.get('next_run_time')) != next_run_time:
        print_warning(f'reschedule_from_child-{id}', next_run_time, result)


# #### Private

def _check_task(primary_id, check_id, primary_time, check_time, range):
    start_range = primary_time - datetime.timedelta(seconds=range)
    end_range = primary_time + datetime.timedelta(seconds=range)
    return primary_id != check_id and check_id != 'heartbeat' and (check_time > start_range)\
        and (check_time < end_range)


def _reschedule_soon_runtime(id):
    jitter = JOB_CONFIG[id]['config']['jitter']
    leeway = JOB_CONFIG[id]['leeway']
    next_run_offset = max(jitter * random.random(), leeway)
    return seconds_from_now_local(next_run_offset)


def _print_tasks(info, printer):
    for id in JOB_CONFIG:
        if id not in info:
            continue
        task_title = id.replace('_', ' ').title()
        timeval = info[id]
        time_from_now = str(timeval - datetime.datetime.now())
        printer("Task Scheduler - %-40s:" % task_title, time_from_now)


def _deconflict_tasks(info, printer):
    for id in JOB_CONFIG:
        timeval = info[id]
        leeway = JOB_CONFIG[id]['leeway']
        dirty = False
        while True:
            # Check for nearby tasks within leeway time and reschedule to avoid having tasks run at the same time
            nearby_tasks = list(filter(lambda x: _check_task(id, x[0], timeval, x[1], leeway), info.items()))
            if len(nearby_tasks) == 0:
                if dirty:
                    printer("Task Scheduler - Conflicted job: %s" % id)
                    info[id] = timeval
                break
            dirty = True
            timeval += datetime.timedelta(seconds=leeway * 2)


def _unlock_tasks(info, locks, manual, printer):
    for id in JOB_CONFIG:
        timeval = info[id]
        is_locked = locks[id].locked
        is_manual = manual[id].manual
        leeway = JOB_CONFIG[id]['leeway']
        # Check if the task is still locked but the next run time is outside the leeway window
        if is_locked and not is_manual and (timeval + datetime.timedelta(seconds=leeway)) > datetime.datetime.now():
            task_title = id.replace('_', ' ').title()
            printer("Unlocking task - %s" % task_title)
            update_job_item(locks[id], False)


def _check_timeout(info, timevals, printer):
    # Detect timeouts from sleep/hibernate and reschedule according to config/leeway and not how apscheduler does it
    timed_out = (time.time() - LAST_CHECK) > 3600.0
    if timed_out:
        printer("Timeout detected!")
    for id in JOB_CONFIG:
        if timed_out and timevals[id].time != 0.0 and time.time() > timevals[id].time:
            printer("Task Scheduler - Missed job: %s" % id)
            jitter = JOB_CONFIG[id]['config']['jitter']
            leeway = JOB_CONFIG[id]['leeway']
            next_run_offset = max(jitter * random.random(), leeway)
            next_run_time = datetime.datetime.now() + datetime.timedelta(seconds=next_run_offset)
            info[id] = next_run_time
        elif timevals[id].time != info[id].timestamp():
            update_job_by_id('job_time', id, {'time': info[id].timestamp()})
