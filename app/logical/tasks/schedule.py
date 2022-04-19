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
from ..check.subscriptions import download_subscription_illusts, download_missing_elements,\
    expire_subscription_elements
from ..records.media_file_rec import batch_delete_media
from ..database.base_db import safe_db_execute
from ..database.subscription_pool_db import get_available_subscription, update_subscription_pool_status
from ..database.subscription_pool_element_db import total_missing_downloads, total_expired_subscription_elements
from ..database.api_data_db import expired_api_data_count, delete_expired_api_data
from ..database.media_file_db import get_expired_media_files, get_all_media_files
from ..database.archive_data_db import expired_archive_data_count, delete_expired_archive_data
from ..database.jobs_db import update_job_lock_status, get_job_lock_status
from ..database.server_info_db import update_last_activity, server_is_busy
from .initialize import initialize_scheduler, recheck_schedule_interval, reschedule_task

# ## GLOBAL DATA

JOB_CONFIG = {
    'expunge_cache_records': {
        'id': 'expunge_cache_records',
        'hours': 8,
        'jitter': 3600,
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
    'check_pending_subscriptions': {
        'id': 'check_pending_subscriptions',
        'hours': 1,
        'jitter': 300,
    },
    'check_pending_downloads': {
        'id': 'check_pending_downloads',
        'hours': 1,
        'jitter': 300,
    },
    'process_expired_subscription_elements': {
        'id': 'process_expired_subscription_elements',
        'hours': 4,
        'jitter': 1200,
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
    'expunge_cache_records': 300,
    'expunge_archive_records': 180,
    'check_all_boorus': 300,
    'check_all_artists_for_boorus': 300,
    'check_all_posts_for_danbooru_id': 300,
    'check_pending_subscriptions': 180,
    'check_pending_downloads': 180,
    'process_expired_subscription_elements': 300,
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


@SCHEDULER.task('interval', **JOB_CONFIG['check_pending_subscriptions'])
def check_pending_subscriptions():
    if not _set_db_semaphore('check_pending_subscriptions'):
        print("Task scheduler - Check All Pending Subscriptions: already running")
        return
    printer = buffered_print("Check All Pending Subscriptions")
    printer("PID:", os.getpid())
    subscriptions = get_available_subscription()
    if len(subscriptions) > 0:
        def try_func(scope_vars):
            download_subscription_illusts(scope_vars['subscription'])

        def msg_func(scope_vars, error):
            return "Unhandled exception occurred on %s: %s" % (scope_vars['subscription'].shortlink, error)

        def finally_func(scope_vars, data, error):
            update_subscription_pool_status(scope_vars['subscription'], 'idle')

        for subscription in subscriptions:
            printer("Processing subscription:", subscription.id)
            update_subscription_pool_status(subscription, 'automatic')
            safe_db_execute('check_pending_subscriptions', 'tasks.schedule', scope_vars={'subscription': subscription},
                            try_func=try_func, msg_func=msg_func, finally_func=finally_func, printer=printer)
    else:
        printer("No subscriptions to process.")
    printer.print()
    _free_db_semaphore('check_pending_subscriptions')


@SCHEDULER.task('interval', **JOB_CONFIG['check_pending_downloads'])
def check_pending_downloads():
    if not _set_db_semaphore('check_pending_downloads'):
        print("Task scheduler - Check All Pending Downloads: already running")
        return
    printer = buffered_print("Check All Pending Downloads")
    printer("PID:", os.getpid())
    total = total_missing_downloads()
    printer("Missing downloads:", total)
    if total > 0:
        download_missing_elements()
    printer.print()
    _free_db_semaphore('check_pending_downloads')


@SCHEDULER.task('interval', **JOB_CONFIG['process_expired_subscription_elements'])
def process_expired_subscription_elements():
    if not _set_db_semaphore('process_expired_subscription_elements'):
        print("Task scheduler - Check All Expired Subscription Elements: already running")
        return
    printer = buffered_print("Process Expired Subscription Elements")
    printer("PID:", os.getpid())
    total = total_expired_subscription_elements()
    if total > 0:
        printer("Expired subscriptions elements:", total)
        safe_db_execute('process_expired_subscription_elements', 'tasks.schedule', printer=printer,
                        try_func=(lambda data: expire_subscription_elements()))
    else:
        printer("No subscriptions elements to process.")
    printer.print()
    _free_db_semaphore('process_expired_subscription_elements')


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
    if not server_is_busy():
        with DB.engine.begin() as connection:
            connection.execute("VACUUM")
            connection.execute("ANALYZE")
    else:
        printer("Server busy, rescheduling....")
        reschedule_task('vacuum_analyze_database', JOB_CONFIG, JOB_LEEWAY)
    printer.print()
    _free_db_semaphore('vacuum_analyze_database')


# #### Private

# ###### Semaphore

def _set_db_semaphore(id):
    status = get_job_lock_status(id)
    if status is None or status:
        return False
    update_job_lock_status(id, True)
    update_last_activity('server')
    return True


def _free_db_semaphore(id):
    update_job_lock_status(id, False)


# ###### Other

@atexit.register
def _cleanup():
    if MAIN_PROCESS:
        RECHECK.cancel()
