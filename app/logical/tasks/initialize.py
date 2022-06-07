# APP/LOGICAL/TASKS/INITIALIZE.PY

# ## PYTHON IMPORTS
import os
import time
import random
import atexit
import datetime

# ## PACKAGE IMPORTS
from utility import RepeatTimer
from utility.time import time_ago
from utility.print import buffered_print

# ## LOCAL IMPORTS
from ... import SCHEDULER
from ..database.server_info_db import get_last_activity
from ..database.jobs_db import create_job_tables, get_all_job_info, delete_job,\
    create_job_enabled, get_all_job_enabled,\
    create_job_lock, get_all_job_locks, update_job_lock_status, delete_lock,\
    create_job_timeval, get_all_job_timevals, update_job_timeval, delete_timeval
from . import JOB_CONFIG, ALL_JOB_INFO, ALL_JOB_ENABLED, ALL_JOB_LOCKS, ALL_JOB_TIMEVALS


# ## GLOBAL VARIABLES

LAST_CHECK = time.time()
RECHECK = None


# ## FUNCTIONS

# #### Main functions

def initialize_all_tasks():
    print("\nInitializing tasks.")
    initialize_task_jobs()
    initialize_task_display()
    initialize_task_cleanup()


def initialize_task_jobs():
    create_job_tables()
    info = _get_initial_job_info()
    enabled = _get_initial_job_enabled()
    locks = _get_initial_job_locks()
    timevals = _get_initial_job_timevals()
    for key in ALL_JOB_TIMEVALS:
        if key not in timevals.keys():
            create_job_timeval(key)
        else:
            update_job_timeval(key, 0.0)
    for key in ALL_JOB_INFO:
        if key in info:
            task_config = JOB_CONFIG[key]['config']
            if info[key] > datetime.datetime.now():
                task_config['next_run_time'] = info[key]
            else:
                print("Task Scheduler - Missed job:", key)
                next_run_time = max(task_config['jitter'] * random.random(), JOB_CONFIG[key]['leeway'])
                task_config['next_run_time'] = datetime.datetime.now() + datetime.timedelta(seconds=next_run_time)
    for key in ALL_JOB_ENABLED:
        if key not in enabled.keys():
            create_job_enabled(key)
    for key in ALL_JOB_LOCKS:
        if key not in locks.keys():
            create_job_lock(key)
        else:
            update_job_lock_status(key, False)


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
    printer = buffered_print("Recheck Schedule Interval")
    printer("PID:", os.getpid())
    printer("Local time:", datetime.datetime.now().ctime())
    user_activity = get_last_activity('user')
    server_activity = get_last_activity('server')
    printer("User last activity:", time_ago(user_activity) if user_activity is not None else None)
    printer("Server last activity:", time_ago(server_activity) if server_activity is not None else None)
    info = get_all_job_info()
    locks = get_all_job_locks()
    timevals = get_all_job_timevals()
    if reschedule:
        _check_timeout(info, timevals, printer)
        _deconflict_tasks(info, printer)
        _unlock_tasks(info, locks, printer)
    _print_tasks(info, printer)
    LAST_CHECK = time.time()
    printer.print()


def reschedule_task(id, reschedule_soon):
    if reschedule_soon:
        jitter = JOB_CONFIG[id]['config']['jitter']
        leeway = JOB_CONFIG[id]['leeway']
        next_run_offset = max(jitter * random.random(), leeway)
        next_run_time = datetime.datetime.now() + datetime.timedelta(seconds=next_run_offset)
    else:
        time_config = {k: v
                       for (k, v) in JOB_CONFIG[id]['config'].items()
                       if k in ['seconds', 'minutes', 'hours', 'days', 'weeks']}
        next_run_time = datetime.datetime.now() + datetime.timedelta(**time_config)
    _reschedule_task(id, next_run_time)


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


def _unlock_tasks(info, locks, printer):
    for id in JOB_CONFIG:
        timeval = info[id]
        leeway = JOB_CONFIG[id]['leeway']
        # Check if the task is still locked but the next run time is outside the leeway window
        if locks[id] and (timeval + datetime.timedelta(seconds=leeway)) > datetime.datetime.now():
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
