# APP/LOGICAL/TASKS/SCHEDULE.PY

# ## PYTHON IMPORTS
import os
import re
import atexit

# ## PACKAGE IMPORTS
from utility import RepeatTimer
from utility.print import buffered_print
from utility.file import get_directory_listing, delete_file

# ## LOCAL IMPORTS
from ... import DB, SCHEDULER, MAIN_PROCESS
from ...models.media_file import CACHE_DATA_DIRECTORY
from ..check.boorus import check_all_boorus
from ..check.posts import check_all_posts_for_danbooru_id
from ..check.booru_artists import check_all_artists_for_boorus
from ..records.media_file_rec import batch_delete_media
from ..database.api_data_db import expired_api_data_count, delete_expired_api_data
from ..database.media_file_db import get_expired_media_files, get_all_media_files
from ..database.archive_data_db import expired_archive_data_count, delete_expired_archive_data
from ..database.jobs_db import update_job_lock_status, get_job_lock_status
from ..database.server_info_db import update_last_activity
from .initialize import initialize_scheduler, recheck_schedule_interval

# ## GLOBAL DATA

JOB_CONFIG = {
    'expunge_cache_records': {
        'id': 'expunge_cache_records',
        'hours': 1,
        'jitter': 300,
    },
    'expunge_archive_records': {
        'id': 'expunge_archive_records',
        'hours': 12,
        'jitter': 3600,
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
    'delete_orphan_images': {
        'id': 'delete_orphan_images',
        'weeks': 1,
        'jitter': 3600,
    },
    'vacuum_analyze_database': {
        'id': 'vacuum_analyze_database',
        'weeks': 1,
        'jitter': 3600,
    },
}

JOB_LEEWAY = {
    'expunge_cache_records': 60,
    'expunge_archive_records': 180,
    'check_all_boorus': 300,
    'check_all_artists_for_boorus': 300,
    'check_all_posts_for_danbooru_id': 300,
    'delete_orphan_images': 300,
    'vacuum_analyze_database': 300,
}


# ## INITIALIZATION

if MAIN_PROCESS:
    # Initialization must take place first, so that the job dictionary can be used to intialize tasks
    print("\nMAIN_PROCESS", os.getpid())
    initialize_scheduler(JOB_CONFIG, JOB_LEEWAY)
    recheck_schedule_interval(JOB_CONFIG, JOB_LEEWAY, False)
    RECHECK = RepeatTimer(300, recheck_schedule_interval, args=(JOB_CONFIG, JOB_LEEWAY, True))
    RECHECK.setDaemon(True)
    RECHECK.start()


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


@SCHEDULER.task("interval", **JOB_CONFIG['expunge_archive_records'])
def expunge_archive_records_task():
    if not _set_db_semaphore('expunge_archive_records'):
        print("Task scheduler - Expunge Archive Records: already running")
        return
    printer = buffered_print("Expunge Archive Records")
    printer("PID:", os.getpid())
    archive_delete_count = expired_archive_data_count()
    printer("Archive data records to delete:", archive_delete_count)
    if archive_delete_count > 0:
        delete_expired_archive_data()
    printer.print()
    _free_db_semaphore('expunge_archive_records')


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


@SCHEDULER.task("interval", **JOB_CONFIG['delete_orphan_images'])
def delete_orphan_images_task():
    if not _set_db_semaphore('delete_orphan_images'):
        print("Task scheduler - Delete Orphan Images: already running")
        return
    printer = buffered_print("Delete Orphan Images")
    printer("PID:", os.getpid())
    dir_listing = get_directory_listing(CACHE_DATA_DIRECTORY)
    dir_md5s = [re.match(r'[0-9a-f]+', x).group(0) for x in dir_listing if re.match(r'[0-9a-f]+\.(jpg|png|gif)', x)]
    cache_md5s = [item.md5 for item in get_all_media_files()]
    bad_md5s = set(dir_md5s).difference(cache_md5s)
    files_deleted = 0
    for filename in dir_listing:
        match = re.match(r'[0-9a-f]+', filename)
        if not match or match.group(0) not in bad_md5s:
            continue
        print("Deleting file:", filename)
        delete_file(os.path.join(CACHE_DATA_DIRECTORY, filename))
        files_deleted += 1
    printer("Files deleted:", files_deleted)
    printer.print()
    _free_db_semaphore('delete_orphan_images')


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


# #### Private

# ###### Semaphore

def _set_db_semaphore(id):
    status = get_job_lock_status(id)
    if status is None or status:
        return False
    update_job_lock_status(id, True)
    update_last_activity()
    return True


def _free_db_semaphore(id):
    update_job_lock_status(id, False)


# ###### Other

@atexit.register
def _cleanup():
    if MAIN_PROCESS:
        RECHECK.cancel()
