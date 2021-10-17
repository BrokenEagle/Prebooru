# APP/LOGICAL/TASKS/SCHEDULE.PY

# ## PYTHON IMPORTS
import os
import random
import datetime

# ## LOCAL IMPORTS
from ... import DB, SCHEDULER, MAIN_PROCESS
from ..utility import seconds_from_now_local, buffered_print
from ..check.boorus import check_all_boorus
from ..check.posts import check_all_posts_for_danbooru_id
from ..check.booru_artists import check_all_artists_for_boorus
from ..records.media_file_rec import batch_delete_media
from ..database.api_data_db import expired_api_data_count, delete_expired_api_data
from ..database.media_file_db import get_expired_media_files
from ..database.jobs_db import get_job_times, delete_job, update_job_next_run_time, create_locks_on_startup,\
    get_job_locks, create_job_lock, update_job_lock_status, get_job_lock_status, delete_lock


# ## GLOBAL DATA

JOB_CONFIG = {
    'expunge_cache_records': {
        'id': 'expunge_cache_records',
        'hours': 1,
        'jitter': 300,
    },
    'check_all_boorus': {
        'id': 'check_all_boorus',
        'days': 1,
        'jitter': 3600,
    },
    'check_all_artists_for_boorus': {
        'id': 'check_all_artists_for_boorus',
        'days': 1,
        'jitter': 3600,
    },
    'check_all_posts_for_danbooru_id': {
        'id': 'check_all_posts_for_danbooru_id',
        'days': 1,
        'jitter': 3600,
    },
    'vacuum_analyze_database': {
        'id': 'vacuum_analyze_database',
        'weeks': 1,
        'jitter': 3600,
    },
    'check_jobs_run_time': {
        'id': 'check_jobs_run_time',
        'minutes': 5,
        'next_run_time': seconds_from_now_local(15),
    },
}

JOB_LEEWAY = {
    'expunge_cache_records': 60,
    'check_all_boorus': 300,
    'check_all_artists_for_boorus': 300,
    'check_all_posts_for_danbooru_id': 300,
    'vacuum_analyze_database': 300,
}


# ## INITIALIZATION

def initialize():
    print("\nInitializing scheduler.")
    create_locks_on_startup()
    times = get_job_times()
    for key in times:
        if key not in JOB_CONFIG:
            print("Task Scheduler - Deleting unused task:", key)
            delete_job(key)
    locks = get_job_locks()
    for key in locks:
        if key not in JOB_CONFIG:
            print("Task Scheduler - Deleting unused lock:", key)
            delete_lock(key)
    for key in JOB_CONFIG:
        if key == 'check_jobs_run_time':
            continue
        if key in times:
            if times[key] > datetime.datetime.now():
                JOB_CONFIG[key]['next_run_time'] = times[key]
            else:
                print("Task Scheduler - Missed job:", key)
                next_run_time = max(JOB_CONFIG[key]['jitter'] * random.random(), JOB_LEEWAY[key])
                JOB_CONFIG[key]['next_run_time'] = datetime.datetime.now() + datetime.timedelta(seconds=next_run_time)
        if key not in locks.keys():
            create_job_lock(key)
        else:
            update_job_lock_status(key, False)


if MAIN_PROCESS:
    # Initialization must take place first, so that the job dictionary can be used to intialize tasks
    initialize()


# ## FUNCTIONS

@SCHEDULER.task("interval", **JOB_CONFIG['expunge_cache_records'])
def expunge_cache_records_task():
    if not _set_db_semaphore('expunge_cache_records'):
        print("Task scheduler - Expunge Cache Records: already running")
        return
    printer = buffered_print("Expunge Cache Records")
    printer("PID:", os.getpid())
    api_delete_count = expired_api_data_count()
    printer("API data records to delete:", api_delete_count)
    if api_delete_count > 0:
        delete_expired_api_data()
    expired_media_records = get_expired_media_files()
    printer("Media files to delete:", len(expired_media_records))
    if len(expired_media_records) > 0:
        batch_delete_media(expired_media_records)
    printer.print()
    _free_db_semaphore('expunge_cache_records')


@SCHEDULER.task('interval', **JOB_CONFIG['check_all_boorus'])
def check_all_boorus_task():
    if not _set_db_semaphore('check_all_boorus'):
        print("Task scheduler - Check All Boorus: already running")
        return
    printer = buffered_print("Check All Boorus")
    printer("PID:", os.getpid())
    check_all_boorus()
    printer.print()
    _free_db_semaphore('check_all_boorus')


@SCHEDULER.task('interval', **JOB_CONFIG['check_all_artists_for_boorus'])
def check_all_artists_for_boorus_task():
    if not _set_db_semaphore('check_all_artists_for_boorus'):
        print("Task scheduler - Check All Artists For Boorus: already running")
        return
    printer = buffered_print("Check All Artists")
    printer("PID:", os.getpid())
    check_all_artists_for_boorus()
    printer.print()
    _free_db_semaphore('check_all_artists_for_boorus')


@SCHEDULER.task('interval', **JOB_CONFIG['check_all_posts_for_danbooru_id'])
def check_all_posts_for_danbooru_id_task():
    if not _set_db_semaphore('check_all_posts_for_danbooru_id'):
        print("Task scheduler - Check All Posts For Danbooru ID: already running")
        return
    printer = buffered_print("Check All Posts")
    printer("PID:", os.getpid())
    check_all_posts_for_danbooru_id()
    printer.print()
    _free_db_semaphore('check_all_posts_for_danbooru_id')


@SCHEDULER.task('interval', **JOB_CONFIG['vacuum_analyze_database'])
def vacuum_analyze_database_task():
    if not _set_db_semaphore('vacuum_analyze_database'):
        print("Task scheduler - Vacuum/analyze DB: already running")
        return
    printer = buffered_print("Vacuum/analyze DB")
    printer("PID:", os.getpid())
    with DB.engine.begin() as connection:
        connection.execute("VACUUM")
        connection.execute("ANALYZE")
    printer.print()
    _free_db_semaphore('vacuum_analyze_database')


@SCHEDULER.task('interval', **JOB_CONFIG['check_jobs_run_time'])
def check_jobs_run_time_task():

    def _check_task(primary_id, check_id, primary_time, check_time, range):
        if primary_id == check_id:
            return False
        start_range = primary_time - datetime.timedelta(seconds=range)
        end_range = primary_time + datetime.timedelta(seconds=range)
        return (check_time > start_range) and (check_time < end_range)

    printer = buffered_print("Check Jobs Run Time")
    printer("PID:", os.getpid())
    times = get_job_times()
    locks = get_job_locks()
    del times['check_jobs_run_time']
    for id in times:
        task_title = id.replace('_', ' ').title()
        timeval = times[id]
        leeway = JOB_LEEWAY[id]
        dirty = False
        while True:
            # Check for nearby tasks within leeway time and reschedule to avoid having tasks run at the same time
            nearby_tasks = list(filter(lambda x: _check_task(id, x[0], timeval, x[1], leeway), times.items()))
            if len(nearby_tasks) == 0:
                if dirty:
                    printer("Updating Run Time - %s" % task_title)
                    times[id] = timeval
                    update_job_next_run_time(id, timeval)
                break
            dirty = True
            timeval += datetime.timedelta(seconds=leeway * 2)
        time_from_now = str(times[id] - datetime.datetime.now())
        printer("Task Scheduler - %-40s:" % task_title, time_from_now)
        # Check if the task is still locked but the next run time is outside the leeway window
        if locks[id] and (timeval + datetime.timedelta(seconds=leeway)) > datetime.datetime.now():
            printer("Unlocking task - %s" % task_title)
            _free_db_semaphore(id)
    printer.print()


# #### Private

def _set_db_semaphore(id):
    status = get_job_lock_status(id)
    if status is None or status:
        return False
    update_job_lock_status(id, True)
    return True


def _free_db_semaphore(id):
    update_job_lock_status(id, False)
