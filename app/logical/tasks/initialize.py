# APP/LOGICAL/TASKS/INITIALIZE.PY

# ## PYTHON IMPORTS
import time
import random
import atexit
import datetime

# ## PACKAGE IMPORTS
from utility import RepeatTimer
from utility.time import local_timezone
from utility.uprint import print_info, print_warning

# ## LOCAL IMPORTS
from ... import SESSION
from ..database.jobs_db import check_tables, get_all_job_items, create_job_item, update_job_item, delete_job_item
from . import JOB_CONFIG, ALL_JOB_INFO, ALL_JOB_ENABLED, ALL_JOB_LOCKS, ALL_JOB_TIMEVALS, ALL_JOB_MANUAL
from .reschedule import recheck_schedule_interval


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
    check_tables()
    _update_job_info()
    _create_or_update_timevals()
    _create_or_update_booleans()
    SESSION.commit()


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


# #### Private

def _update_job_info():
    info = _get_initial_job_info()
    for key in ALL_JOB_INFO:
        if key in info:
            task_config = JOB_CONFIG[key]['config']
            if info[key] > datetime.datetime.now():
                task_config['next_run_time'] = info[key].replace(tzinfo=local_timezone())
            else:
                print_warning("Task Scheduler - Missed job:", key)
                jitter_time = max(task_config['jitter'] * random.random(), JOB_CONFIG[key]['leeway'])
                jitter_delta = datetime.timedelta(seconds=jitter_time)
                task_config['next_run_time'] = datetime.datetime.now(local_timezone()) + jitter_delta


def _get_initial_job_info():
    info = get_all_job_items('job_info')
    for id, item in info.items():
        if id not in ALL_JOB_INFO:
            print("Task Scheduler - Deleting unused task:", id)
            delete_job_item(item)
    return {item.id: item.next_run_time for item in info.values()}


def _get_initial_job_enabled():
    all_enabled = get_all_job_items('job_enable')
    for id, item in all_enabled.items():
        if id not in ALL_JOB_ENABLED:
            print("Task Scheduler - Deleting unused enabled:", id)
            delete_job_item(item)
    return all_enabled


def _get_initial_job_manual():
    all_manual = get_all_job_items('job_manual')
    for id, item in all_manual.items():
        if id not in ALL_JOB_MANUAL:
            print("Task Scheduler - Deleting unused manual:", id)
            delete_job_item(item)
    return all_manual


def _get_initial_job_locks():
    all_locks = get_all_job_items('job_lock')
    for id, item in all_locks.items():
        if id not in ALL_JOB_LOCKS:
            print("Task Scheduler - Deleting unused lock:", id)
            delete_job_item(item)
    return all_locks


def _get_initial_job_timevals():
    all_timevals = get_all_job_items('job_time')
    for id, item in all_timevals.items():
        if id not in ALL_JOB_TIMEVALS:
            print("Task Scheduler - Deleting unused timeval:", id)
            delete_job_item(item)
    return all_timevals


def _create_or_update_timevals():
    timevals = _get_initial_job_timevals()
    for key in ALL_JOB_TIMEVALS:
        if key not in timevals.keys():
            create_job_item('job_time', key, 0.0)
        else:
            update_job_item(timevals[key], 0.0)


def _create_or_update_booleans():
    enabled = _get_initial_job_enabled()
    manual = _get_initial_job_manual()
    locks = _get_initial_job_locks()
    for key in ALL_JOB_ENABLED:
        if key not in enabled.keys():
            create_job_item('job_enable', key, True)
    for key in ALL_JOB_MANUAL:
        if key not in manual.keys():
            create_job_item('job_manual', key, False)
        else:
            update_job_item(manual[key], False)
    for key in ALL_JOB_LOCKS:
        if key not in locks.keys():
            create_job_item('job_lock', key, False)
        else:
            update_job_item(locks[key], False)
