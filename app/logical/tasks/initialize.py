# APP/LOGICAL/TASKS/INITIALIZE.PY

# ## PYTHON IMPORTS
import os
import time
import random
import datetime

# ## PACKAGE IMPORTS
from utility.time import time_ago
from utility.print import buffered_print

# ## LOCAL IMPORTS
from ... import SCHEDULER
from ..database.server_info_db import get_last_activity
from ..database.jobs_db import create_job_tables, get_all_job_info, delete_job, create_job_lock, get_all_job_locks,\
    update_job_lock_status, delete_lock, create_job_timeval, get_all_job_timevals,\
    update_job_timeval, delete_timeval

# ## GLOBAL VARIABLES

LAST_CHECK = time.time()


# ## FUNCTIONS

# #### Main functions

def initialize_scheduler(config, leeway):
    print("\nInitializing scheduler.")
    create_job_tables()
    info = _get_initial_job_info(config)
    locks = _get_initial_job_locks(config)
    timevals = _get_initial_job_timevals(config)
    for key in config:
        if key not in timevals.keys():
            create_job_timeval(key)
        else:
            update_job_timeval(key, 0.0)
        if key in info:
            if info[key] > datetime.datetime.now():
                config[key]['next_run_time'] = info[key]
            else:
                print("Task Scheduler - Missed job:", key)
                next_run_time = max(config[key]['jitter'] * random.random(), leeway[key])
                config[key]['next_run_time'] = datetime.datetime.now() + datetime.timedelta(seconds=next_run_time)
        if key not in locks.keys():
            create_job_lock(key)
        else:
            update_job_lock_status(key, False)


def recheck_schedule_interval(config, lconfig, reschedule):
    global LAST_CHECK
    printer = buffered_print("Recheck Schedule Interval")
    printer("PID:", os.getpid())
    user_activity = get_last_activity('user')
    server_activity = get_last_activity('server')
    printer("User last activity:", time_ago(user_activity) if user_activity is not None else None)
    printer("Server last activity:", time_ago(server_activity) if server_activity is not None else None)
    info = get_all_job_info()
    locks = get_all_job_locks()
    timevals = get_all_job_timevals()
    if reschedule:
        _check_timeout(config, lconfig, info, timevals, printer)
        _deconflict_tasks(config, lconfig, info, locks, printer)
        _unlock_tasks(config, lconfig, info, locks, printer)
    _print_tasks(config, lconfig, info, locks, printer)
    LAST_CHECK = time.time()
    printer.print()


def reschedule_task(id, config, lconfig):
    next_run_offset = max(config[id]['jitter'] * random.random(), lconfig[id])
    next_run_time = datetime.datetime.now() + datetime.timedelta(seconds=next_run_offset)
    _reschedule_task(id, next_run_time)


# #### Private

# ###### Initialize

def _get_initial_job_info(config):
    info = get_all_job_info()
    for id in info:
        if id not in config and id != 'heartbeat':
            print("Task Scheduler - Deleting unused task:", id)
            delete_job(id)
    return info


def _get_initial_job_locks(config):
    locks = get_all_job_locks()
    for id in locks:
        if id not in config:
            print("Task Scheduler - Deleting unused lock:", id)
            delete_lock(id)
    return locks


def _get_initial_job_timevals(config):
    timevals = get_all_job_timevals()
    for id in timevals:
        if id not in config:
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


def _print_tasks(config, lconfig, info, locks, printer):
    for id in config:
        if id not in info:
            continue
        task_title = id.replace('_', ' ').title()
        timeval = info[id]
        time_from_now = str(timeval - datetime.datetime.now())
        printer("Task Scheduler - %-40s:" % task_title, time_from_now)


def _deconflict_tasks(config, lconfig, info, locks, printer):
    for id in config:
        timeval = info[id]
        leeway = lconfig[id]
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


def _unlock_tasks(config, lconfig, info, locks, printer):
    for id in config:
        task_title = id.replace('_', ' ').title()
        timeval = info[id]
        leeway = lconfig[id]
        # Check if the task is still locked but the next run time is outside the leeway window
        if locks[id] and (timeval + datetime.timedelta(seconds=leeway)) > datetime.datetime.now():
            printer("Unlocking task - %s" % task_title)
            update_job_lock_status(id, False)


def _check_timeout(config, lconfig, info, timevals, printer):
    # Detect timeouts from sleep/hibernate and reschedule according to config/leeway and not how apscheduler does it
    timed_out = (time.time() - LAST_CHECK) > 3600.0
    if timed_out:
        printer("Timeout detected!")
    for id in config:
        if timed_out and timevals[id] != 0.0 and time.time() > timevals[id]:
            printer("Task Scheduler - Missed job: %s" % id)
            next_run_offset = max(config[id]['jitter'] * random.random(), lconfig[id])
            next_run_time = datetime.datetime.now() + datetime.timedelta(seconds=next_run_offset)
            _reschedule_task(id, next_run_time)
            info[id] = next_run_time
        else:
            update_job_timeval(id, info[id].timestamp())
