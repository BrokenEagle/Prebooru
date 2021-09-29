# APP/LOGICAL/TASKS/SCHEDULE.PY

# ## PYTHON IMPORTS
import os
import datetime

# ## EXTERNAL IMPORTS
from sqlalchemy import select

# ## LOCAL IMPORTS
from ... import DB, SCHEDULER, SCHEDULER_JOBSTORES, MAIN_PROCESS
from ..utility import buffered_print
from ..check.boorus import check_all_boorus
from ..check.posts import check_all_posts_for_danbooru_id
from ..check.booru_artists import check_all_artists_for_boorus
from ..records.media_file_rec import batch_delete_media
from ..database.api_data_db import expired_api_data_count, delete_expired_api_data
from ..database.media_file_db import get_expired_media_files


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
        'id': 'check_all_artists_for_boorus',
        'days': 1,
        'jitter': 3600,
    },
    'vacuum_analyze_database': {
        'id': 'vacuum_analyze_database',
        'days': 1,
        'jitter': 3600,
    },
}


# ## INITIALIZATION

def initialize():
    print("\nInitializing scheduler.")
    with SCHEDULER_JOBSTORES.engine.begin() as conn:
        statement = select([SCHEDULER_JOBSTORES.jobs_t.c.id, SCHEDULER_JOBSTORES.jobs_t.c.next_run_time])
        timestamps = conn.execute(statement).fetchall()
        timedict = {f[0]: datetime.datetime.fromtimestamp(f[1]) for f in timestamps}
        for key in timedict:
            if key not in JOB_CONFIG:
                print("Task Scheduler - Deleting unused key:", key)
                statement = SCHEDULER_JOBSTORES.jobs_t.delete().where(SCHEDULER_JOBSTORES.jobs_t.c.id == key)
                conn.execute(statement)
    for key in JOB_CONFIG:
        if key in timedict and timedict[key] > datetime.datetime.now():
            JOB_CONFIG[key]['next_run_time'] = timedict[key]
            task_title = key.replace('_', ' ').title()
            time_from_now = str(JOB_CONFIG[key]['next_run_time'] - datetime.datetime.now())
            print("Task Scheduler - %s:" % task_title, time_from_now)


if MAIN_PROCESS:
    initialize()


# ## FUNCTIONS

@SCHEDULER.task("interval", **JOB_CONFIG['expunge_cache_records'])
def expunge_cache_records_task():
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


@SCHEDULER.task('interval', **JOB_CONFIG['check_all_boorus'])
def check_all_boorus_task():
    printer = buffered_print("Check All Boorus")
    printer("PID:", os.getpid())
    check_all_boorus(printer=printer)
    printer.print()


@SCHEDULER.task('interval', **JOB_CONFIG['check_all_artists_for_boorus'])
def check_all_artists_for_boorus_task():
    printer = buffered_print("Check All Artists")
    printer("PID:", os.getpid())
    check_all_artists_for_boorus()
    printer.print()


@SCHEDULER.task('interval', **JOB_CONFIG['check_all_posts_for_danbooru_id'])
def check_all_posts_for_danbooru_id_task():
    printer = buffered_print("Check All Posts")
    printer("PID:", os.getpid())
    check_all_posts_for_danbooru_id()
    printer.print()


@SCHEDULER.task('interval', **JOB_CONFIG['vacuum_analyze_database'])
def vacuum_analyze_database_task():
    printer = buffered_print("Vacuum/analyze DB")
    printer("PID:", os.getpid())
    with DB.engine.begin() as connection:
        connection.execute("VACUUM")
        connection.execute("ANALYZE")
    printer.print()
