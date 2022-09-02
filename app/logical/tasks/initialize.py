# APP/LOGICAL/TASKS/INITIALIZE.PY

# ## PYTHON IMPORTS
import os
import time
import random
import atexit
import datetime

# ## PACKAGE IMPORTS
from utility import RepeatTimer
from utility.time import time_ago, seconds_from_now_local, process_utc_timestring
from utility.print import buffered_print, print_info, print_warning, print_error

# ## LOCAL IMPORTS
from ... import SCHEDULER
from ..logger import log_error
from ..network import prebooru_json_request
from ..database.server_info_db import get_last_activity
from ..database.jobs_db import create_job_tables, get_all_job_info, delete_job,\
    create_job_enabled, get_all_job_enabled, get_all_job_manual, create_job_manual,\
    create_job_lock, get_all_job_locks, update_job_lock_status, delete_lock,\
    create_job_timeval, get_all_job_timevals, update_job_timeval, delete_timeval,\
    update_job_manual_status
from . import JOB_CONFIG, ALL_JOB_INFO, ALL_JOB_ENABLED, ALL_JOB_LOCKS, ALL_JOB_TIMEVALS,\
    ALL_JOB_MANUAL


# ## GLOBAL VARIABLES

LAST_CHECK = time.time()
RECHECK = None


# ## FUNCTIONS

# #### Main functions

def initialize_all_tasks():
    print_info("\nInitializing tasks.")
    initialize_task_jobs()
    initialize_task_display()
    initialize_task_cleanup()


def initialize_task_jobs():
    create_job_tables()
    _update_job_info()
    _create_or_update_timevals()
    _create_or_update_booleans()


def initialize_task_display():
    global RECHECK
    recheck_schedule_interval(False)
    RECHECK = RepeatTimer(300, recheck_schedule_interval, args=(True,))
    RECHECK.setDaemon(True)
    RECHECK.start()


def initialize_task_cleanup():
    @atexit.register
    def _cleanup():
        RECHECK.cancel()


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
    locks = get_all_job_locks()
    manual = get_all_job_locks()
    timevals = get_all_job_timevals()
    if reschedule:
        _check_timeout(info, timevals, printer)
        _deconflict_tasks(info, printer)
        _unlock_tasks(info, locks, manual, printer)
    _print_tasks(info, printer)
    LAST_CHECK = time.time()
    printer.print()


def reschedule_task(id, reschedule_soon):
    if reschedule_soon:
        next_run_time = _reschedule_soon_runtime(id)
    else:
        time_config = {k: v
                       for (k, v) in JOB_CONFIG[id]['config'].items()
                       if k in ['seconds', 'minutes', 'hours', 'days', 'weeks']}
        next_run_time = datetime.datetime.now() + datetime.timedelta(**time_config)
    _reschedule_task(id, next_run_time)


def reschedule_from_child(id):
    """A child does not have access to the scheduler, so it must notify the parent."""
    next_run_time = _reschedule_soon_runtime(id)
    data = {'next_run_time': next_run_time.isoformat(timespec='seconds')}
    result = prebooru_json_request(f'/scheduler/jobs/{id}', 'patch', json=data)
    if not isinstance(result, dict):
        print_error(f'reschedule_from_child-{id}', result)
        log_error('tasks.initialize.reschedule_from_child', f"Error rescheduling {id}:\n" + str(result))
    if result.get('id') != id or process_utc_timestring(result.get('next_run_time')) != next_run_time:
        print_warning(f'reschedule_from_child-{id}', next_run_time, result)


# #### Private

# ###### Initialize

def _get_initial_job_info():
    info = get_all_job_info()
    for id in info:
        if id not in ALL_JOB_INFO:
            print("Task Scheduler - Deleting unused task:", id)
            delete_job(id)
    return info


def _get_initial_job_enabled():
    enabled = get_all_job_enabled()
    for id in enabled:
        if id not in ALL_JOB_ENABLED:
            print("Task Scheduler - Deleting unused enabled:", id)
            delete_lock(id)
    return enabled


def _get_initial_job_manual():
    manual = get_all_job_manual()
    for id in manual:
        if id not in ALL_JOB_MANUAL:
            print("Task Scheduler - Deleting unused manual:", id)
            delete_lock(id)
    return manual


def _get_initial_job_locks():
    locks = get_all_job_locks()
    for id in locks:
        if id not in ALL_JOB_LOCKS:
            print("Task Scheduler - Deleting unused lock:", id)
            delete_lock(id)
    return locks


def _get_initial_job_timevals():
    timevals = get_all_job_timevals()
    for id in timevals:
        if id not in ALL_JOB_TIMEVALS:
            print("Task Scheduler - Deleting unused timeval:", id)
            delete_timeval(id)
    return timevals


# ###### Check tasks

def _check_task(primary_id, check_id, primary_time, check_time, range):
    start_range = primary_time - datetime.timedelta(seconds=range)
    end_range = primary_time + datetime.timedelta(seconds=range)
    return primary_id != check_id and check_id != 'heartbeat' and (check_time > start_range)\
        and (check_time < end_range)


def _reschedule_task(id, next_run_time):
    SCHEDULER.modify_job(id, 'default', next_run_time=next_run_time)
    # update_job_next_run_time(id, next_run_time.timestamp())
    update_job_timeval(id, next_run_time.timestamp())


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
                    _reschedule_task(id, timeval)
                    info[id] = timeval
                break
            dirty = True
            timeval += datetime.timedelta(seconds=leeway * 2)


def _unlock_tasks(info, locks, manual, printer):
    for id in JOB_CONFIG:
        timeval = info[id]
        leeway = JOB_CONFIG[id]['leeway']
        # Check if the task is still locked but the next run time is outside the leeway window
        if locks[id] and not manual[id] and (timeval + datetime.timedelta(seconds=leeway)) > datetime.datetime.now():
            task_title = id.replace('_', ' ').title()
            printer("Unlocking task - %s" % task_title)
            update_job_lock_status(id, False)


def _check_timeout(info, timevals, printer):
    # Detect timeouts from sleep/hibernate and reschedule according to config/leeway and not how apscheduler does it
    timed_out = (time.time() - LAST_CHECK) > 3600.0
    if timed_out:
        printer("Timeout detected!")
    for id in JOB_CONFIG:
        if timed_out and timevals[id] != 0.0 and time.time() > timevals[id]:
            printer("Task Scheduler - Missed job: %s" % id)
            jitter = JOB_CONFIG[id]['config']['jitter']
            leeway = JOB_CONFIG[id]['leeway']
            next_run_offset = max(jitter * random.random(), leeway)
            next_run_time = datetime.datetime.now() + datetime.timedelta(seconds=next_run_offset)
            _reschedule_task(id, next_run_time)
            info[id] = next_run_time
        else:
            update_job_timeval(id, info[id].timestamp())


def _update_job_info():
    info = _get_initial_job_info()
    for key in ALL_JOB_INFO:
        if key in info:
            task_config = JOB_CONFIG[key]['config']
            if info[key] > datetime.datetime.now():
                task_config['next_run_time'] = info[key]
            else:
                print_warning("Task Scheduler - Missed job:", key)
                next_run_time = max(task_config['jitter'] * random.random(), JOB_CONFIG[key]['leeway'])
                task_config['next_run_time'] = datetime.datetime.now() + datetime.timedelta(seconds=next_run_time)


def _create_or_update_timevals():
    timevals = _get_initial_job_timevals()
    for key in ALL_JOB_TIMEVALS:
        if key not in timevals.keys():
            create_job_timeval(key)
        else:
            update_job_timeval(key, 0.0)


def _create_or_update_booleans():
    enabled = _get_initial_job_enabled()
    manual = _get_initial_job_manual()
    locks = _get_initial_job_locks()
    for key in ALL_JOB_ENABLED:
        if key not in enabled.keys():
            create_job_enabled(key)
    for key in ALL_JOB_MANUAL:
        if key not in manual.keys():
            create_job_manual(key)
        else:
            update_job_manual_status(key, False)
    for key in ALL_JOB_LOCKS:
        if key not in locks.keys():
            create_job_lock(key)
        else:
            update_job_lock_status(key, False)
