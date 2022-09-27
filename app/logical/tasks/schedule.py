# APP/LOGICAL/TASKS/SCHEDULE.PY

# ## PYTHON IMPORTS
import os
import re
import time

# ## PACKAGE IMPORTS
from config import ALTERNATE_MEDIA_DIRECTORY
from utility.print import buffered_print, print_info
from utility.file import get_directory_listing, delete_file
from utility.time import seconds_from_now_local

# ## LOCAL IMPORTS
from ... import DB, SCHEDULER
from ...models.media_file import CACHE_DATA_DIRECTORY
from ..check.subscriptions import download_subscription_illusts, download_missing_elements,\
    expire_subscription_elements
from ..records.post_rec import relocate_old_posts_to_alternate, check_all_posts_for_danbooru_id
from ..records.artist_rec import check_all_artists_for_boorus
from ..records.booru_rec import check_all_boorus
from ..records.media_file_rec import batch_delete_media
from ..database.base_db import safe_db_execute
from ..database.subscription_db import get_available_subscription, update_subscription_status,\
    update_subscription_active, get_busy_subscriptions, get_subscription_by_ids
from ..database.subscription_element_db import total_missing_downloads, total_expired_subscription_elements
from ..database.api_data_db import expired_api_data_count, delete_expired_api_data
from ..database.media_file_db import get_expired_media_files, get_all_media_files
from ..database.archive_db import expired_archive_count, delete_expired_archive
from ..database.jobs_db import get_job_enabled_status, update_job_lock_status, get_job_lock_status,\
    get_job_manual_status
from ..database.server_info_db import update_last_activity, server_is_busy, get_subscriptions_ready,\
    update_subscriptions_ready
from .initialize import reschedule_from_child, schedule_from_child
from . import JOB_CONFIG


# ## FUNCTIONS

# #### Interval tasks

@SCHEDULER.task("interval", **JOB_CONFIG['expunge_cache_records']['config'])
def expunge_cache_records_task():
    if not get_job_enabled_status('expunge_cache_records'):
        print("Task scheduler - Expunge Cache Records: disabled")
        return
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


@SCHEDULER.task("interval", **JOB_CONFIG['expunge_archive_records']['config'])
def expunge_archive_records_task():
    if not get_job_enabled_status('expunge_archive_records'):
        print("Task scheduler - Expunge Archive Records: disabled")
        return
    if not _set_db_semaphore('expunge_archive_records'):
        print("Task scheduler - Expunge Archive Records: already running")
        return
    printer = buffered_print("Expunge Archive Records")
    printer("PID:", os.getpid())
    archive_delete_count = expired_archive_count()
    printer("Archive data records to delete:", archive_delete_count)
    if archive_delete_count > 0:
        delete_expired_archive()
    printer.print()
    _free_db_semaphore('expunge_archive_records')


@SCHEDULER.task('interval', **JOB_CONFIG['check_all_boorus']['config'])
def check_all_boorus_task():
    if not get_job_enabled_status('check_all_boorus'):
        print("Task scheduler - Check All Boorus: disabled")
        return
    if not _set_db_semaphore('check_all_boorus'):
        print("Task scheduler - Check All Boorus: already running")
        return
    printer = buffered_print("Check All Boorus")
    printer("PID:", os.getpid())
    check_all_boorus()
    printer.print()
    _free_db_semaphore('check_all_boorus')


@SCHEDULER.task('interval', **JOB_CONFIG['check_all_artists_for_boorus']['config'])
def check_all_artists_for_boorus_task():
    if not get_job_enabled_status('check_all_artists_for_boorus'):
        print("Task scheduler - Check All Artists for Boorus: disabled")
        return
    if not _set_db_semaphore('check_all_artists_for_boorus'):
        print("Task scheduler - Check All Artists For Boorus: already running")
        return
    printer = buffered_print("Check All Artists")
    printer("PID:", os.getpid())
    check_all_artists_for_boorus()
    printer.print()
    _free_db_semaphore('check_all_artists_for_boorus')


@SCHEDULER.task('interval', **JOB_CONFIG['check_all_posts_for_danbooru_id']['config'])
def check_all_posts_for_danbooru_id_task():
    if not get_job_enabled_status('check_all_posts_for_danbooru_id'):
        print("Task scheduler - Check All Posts for Danbooru ID: disabled")
        return
    if not _set_db_semaphore('check_all_posts_for_danbooru_id'):
        print("Task scheduler - Check All Posts For Danbooru ID: already running")
        return
    printer = buffered_print("Check All Posts")
    printer("PID:", os.getpid())
    check_all_posts_for_danbooru_id()
    printer.print()
    _free_db_semaphore('check_all_posts_for_danbooru_id')


@SCHEDULER.task('interval', **JOB_CONFIG['check_pending_subscriptions']['config'])
def check_pending_subscriptions():
    if not get_subscriptions_ready():
        print("Task scheduler - Subscription reset not yet initiated.")
        return
    if not get_job_enabled_status('check_pending_subscriptions'):
        print("Task scheduler - Check Pending Subscriptions: disabled")
        return
    if not _set_db_semaphore('check_pending_subscriptions'):
        print("Task scheduler - Check All Pending Subscriptions: already running")
        return
    manual = get_job_manual_status('check_pending_subscriptions')
    printer = buffered_print("Check All Pending Subscriptions")
    printer("PID:", os.getpid())
    subscriptions = get_available_subscription(manual)
    if len(subscriptions) > 0:
        schedule_from_child('subscriptions-callback', 'app.logical.tasks.schedule:_pending_subscription_callback',
                            [subscription.id for subscription in subscriptions], seconds_from_now_local(900))
        for subscription in subscriptions:
            printer("Processing subscription:", subscription.id)
            _process_pending_subscription(subscription, printer)
    else:
        printer("No subscriptions to process.")
    printer.print()
    _free_db_semaphore('check_pending_subscriptions')


@SCHEDULER.task('interval', **JOB_CONFIG['check_pending_downloads']['config'])
def check_pending_downloads():
    if not get_subscriptions_ready():
        print("Task scheduler - Subscription reset not yet initiated.")
        return
    if not get_job_enabled_status('check_pending_downloads'):
        print("Task scheduler - Check Pending Downloads: disabled")
        return
    if not _set_db_semaphore('check_pending_downloads'):
        print("Task scheduler - Check All Pending Downloads: already running")
        return
    printer = buffered_print("Check All Pending Downloads")
    printer("PID:", os.getpid())
    total = total_missing_downloads()
    printer("Missing downloads:", total)
    if total > 0:
        manual = get_job_manual_status('check_pending_downloads')
        download_missing_elements(manual)
    printer.print()
    _free_db_semaphore('check_pending_downloads')


@SCHEDULER.task('interval', **JOB_CONFIG['process_expired_subscription_elements']['config'])
def process_expired_subscription_elements():
    if not get_job_enabled_status('process_expired_subscription_elements'):
        print("Task scheduler - Process Expired Subscription Elements: disabled")
        return
    if not _set_db_semaphore('process_expired_subscription_elements'):
        print("Task scheduler - Check All Expired Subscription Elements: already running")
        return
    printer = buffered_print("Process Expired Subscription Elements")
    printer("PID:", os.getpid())
    total = total_expired_subscription_elements()
    if total > 0:
        manual = get_job_manual_status('process_expired_subscription_elements')
        printer("Expired subscriptions elements:", total)
        start = time.time()
        data = safe_db_execute('process_expired_subscription_elements', 'tasks.schedule', printer=printer,
                               try_func=(lambda data: expire_subscription_elements(manual)))
        print("expire_subscription_elements results:", data)
        print("Task duration:", time.time() - start)
    else:
        printer("No subscriptions elements to process.")
    printer.print()
    _free_db_semaphore('process_expired_subscription_elements')


@SCHEDULER.task("interval", **JOB_CONFIG['relocate_old_posts']['config'])
def relocate_old_posts_task():
    if not get_job_enabled_status('relocate_old_posts'):
        print("Task scheduler - Relocate Old Posts: disabled")
        return
    if not _set_db_semaphore('relocate_old_posts'):
        print("Task scheduler - Relocate Old Posts: already running")
        return
    printer = buffered_print("Relocate Old Posts")
    printer("PID:", os.getpid())
    if ALTERNATE_MEDIA_DIRECTORY is None:
        printer("Alternate media directory not configured.")
    elif not os.path.exists(ALTERNATE_MEDIA_DIRECTORY):
        printer("Alternate media directory not found.")
    else:
        manual = get_job_manual_status('relocate_old_posts')
        start = time.time()
        posts_moved = relocate_old_posts_to_alternate(manual)
        if posts_moved is None:
            printer("Alternate move days not configured.")
        else:
            printer("Posts moved:", posts_moved)
        printer("Task duration:", time.time() - start)
    printer.print()
    _free_db_semaphore('relocate_old_posts')


@SCHEDULER.task("interval", **JOB_CONFIG['delete_orphan_images']['config'])
def delete_orphan_images_task():
    if not get_job_enabled_status('delete_orphan_images'):
        print("Task scheduler - Delete Orphan Images: disabled")
        return
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


@SCHEDULER.task('interval', **JOB_CONFIG['vacuum_analyze_database']['config'])
def vacuum_analyze_database_task():
    manual = get_job_manual_status('vacuum_analyze_database')
    if not manual and server_is_busy():
        print("Vaccuum/Analyze: Server busy, rescheduling....")
        reschedule_from_child('vacuum_analyze_database')
        return
    if not _set_db_semaphore('vacuum_analyze_database'):
        print("Task scheduler - Vacuum/analyze DB: already running")
        return
    printer = buffered_print("Vacuum/analyze DB")
    printer("PID:", os.getpid())
    start_time = time.time()
    with DB.engine.begin() as connection:
        connection.execute("VACUUM")
        connection.execute("ANALYZE")
    printer("Execution time:", time.time() - start_time)
    printer.print()
    _free_db_semaphore('vacuum_analyze_database')


# #### Startup tasks

@SCHEDULER.task('date', id="reset_subscription_status", next_run_time=seconds_from_now_local(60))
def reset_subscription_status_task():
    printer = buffered_print("Reset Subscription Status")
    printer("PID:", os.getpid())
    subscriptions = get_busy_subscriptions()
    for subscription in subscriptions:
        update_subscription_status(subscription, 'idle')
    printer("Subscriptions reset:", len(subscriptions))
    printer.print()
    update_subscriptions_ready(True)


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


def _process_pending_subscription(subscription, printer):
    def try_func(scope_vars):
        nonlocal subscription
        download_subscription_illusts(subscription)

    def msg_func(scope_vars, error):
        nonlocal subscription
        return "Unhandled exception occurred on %s: %s" % (subscription.shortlink, error)

    def error_func(scope_vars, error):
        nonlocal subscription
        update_subscription_status(subscription, 'error')
        update_subscription_active(subscription, False)

    def finally_func(scope_vars, error, data):
        nonlocal subscription
        if error is None and subscription.status != 'error':
            update_subscription_status(subscription, 'idle')

    update_subscription_status(subscription, 'automatic')
    safe_db_execute('check_pending_subscriptions', 'tasks.schedule', scope_vars={'subscription': subscription},
                    try_func=try_func, msg_func=msg_func, error_func=error_func, finally_func=finally_func,
                    printer=printer)


def _pending_subscription_callback(subscription_ids):
    print_info('pending_subscription_callback', subscription_ids)
    subscriptions = get_subscription_by_ids(subscription_ids)
    for subscription in subscriptions:
        if subscription.status == 'automatic':
            update_subscription_status(subscription, 'idle')
