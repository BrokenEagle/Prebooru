# APP/LOGICAL/TASKS/SCHEDULE.PY

# ## PYTHON IMPORTS
import os
import re
import time

# ## PACKAGE IMPORTS
from config import ALTERNATE_MEDIA_DIRECTORY
from utility.uprint import buffered_print, print_info
from utility.file import get_directory_listing, delete_file
from utility.time import seconds_from_now_local

# ## LOCAL IMPORTS
from ... import DB, SESSION, SCHEDULER
from ...models.media_file import CACHE_DATA_DIRECTORY
from ..records.post_rec import relocate_old_posts_to_alternate, check_all_posts_for_danbooru_id
from ..records.artist_rec import check_all_artists_for_boorus
from ..records.booru_rec import check_all_boorus
from ..records.media_file_rec import batch_delete_media
from ..records.subscription_rec import download_subscription_illusts, download_missing_elements,\
    unlink_expired_subscription_elements, delete_expired_subscription_elements, archive_expired_subscription_elements
from ..database.base_db import safe_db_execute
from ..database.subscription_db import get_available_subscription, update_subscription_status,\
    update_subscription_active, get_busy_subscriptions, get_subscription_by_ids
from ..database.subscription_element_db import total_missing_downloads, expired_subscription_elements
from ..database.api_data_db import expired_api_data_count, delete_expired_api_data
from ..database.media_file_db import get_expired_media_files, get_all_media_files
from ..database.archive_db import expired_archive_count, delete_expired_archive
from ..database.jobs_db import get_job_item, update_job_item, update_job_by_id
from ..database.server_info_db import update_last_activity, server_is_busy, get_subscriptions_ready,\
    update_subscriptions_ready
from .initialize import reschedule_from_child, schedule_from_child
from . import JOB_CONFIG


# ## FUNCTIONS

# #### Interval tasks

@SCHEDULER.task("interval", **JOB_CONFIG['expunge_cache_records']['config'])
def expunge_cache_records_task():
    def _task(printer):
        api_delete_count = expired_api_data_count()
        printer("API data records to delete:", api_delete_count)
        if api_delete_count > 0:
            delete_expired_api_data()
        expired_media_records = get_expired_media_files()
        printer("Media files to delete:", len(expired_media_records))
        if len(expired_media_records) > 0:
            batch_delete_media(expired_media_records)

    _execute_scheduled_task(_task, 'expunge_cache_records', True, True)


@SCHEDULER.task("interval", **JOB_CONFIG['expunge_archive_records']['config'])
def expunge_archive_records_task():
    def _task(printer):
        archive_delete_count = expired_archive_count()
        printer("Archive data records to delete:", archive_delete_count)
        if archive_delete_count > 0:
            delete_expired_archive()

    _execute_scheduled_task(_task, 'expunge_archive_records', True, True)


@SCHEDULER.task('interval', **JOB_CONFIG['check_all_boorus']['config'])
def check_all_boorus_task():
    def _task(printer):
        check_all_boorus()

    _execute_scheduled_task(_task, 'check_all_boorus', True, True)


@SCHEDULER.task('interval', **JOB_CONFIG['check_all_artists_for_boorus']['config'])
def check_all_artists_for_boorus_task():
    def _task(printer):
        check_all_artists_for_boorus()

    _execute_scheduled_task(_task, 'check_all_artists_for_boorus', True, True)


@SCHEDULER.task('interval', **JOB_CONFIG['check_all_posts_for_danbooru_id']['config'])
def check_all_posts_for_danbooru_id_task():
    def _task(printer):
        check_all_posts_for_danbooru_id()

    _execute_scheduled_task(_task, 'check_all_posts_for_danbooru_id', True, True)


@SCHEDULER.task('interval', **JOB_CONFIG['check_pending_subscriptions']['config'])
def check_pending_subscriptions_task():
    def _task(printer):
        manual = _is_job_manual('check_pending_subscriptions')
        subscriptions = get_available_subscription(manual)
        if len(subscriptions) > 0:
            schedule_from_child('subscriptions-callback', 'app.logical.tasks.schedule:_pending_subscription_callback',
                                [subscription.id for subscription in subscriptions], seconds_from_now_local(900))
            for subscription in subscriptions:
                printer("Processing subscription:", subscription.id)
                _process_pending_subscription(subscription, printer)
        else:
            printer("No subscriptions to process.")

    if _subscriptions_check():
        _execute_scheduled_task(_task, 'check_pending_subscriptions', True, True)


@SCHEDULER.task('interval', **JOB_CONFIG['check_pending_downloads']['config'])
def check_pending_downloads_task():
    def _task(printer):
        total = total_missing_downloads()
        printer("Missing downloads:", total)
        if total > 0:
            manual = _is_job_manual('check_pending_downloads')
            processed = download_missing_elements(manual)
            printer("Elements processed:", processed)

    if _subscriptions_check():
        _execute_scheduled_task(_task, 'check_pending_downloads', True, True)


@SCHEDULER.task('interval', **JOB_CONFIG['unlink_expired_subscription_elements']['config'])
def unlink_expired_subscription_elements_task():
    def _task(printer):
        total = expired_subscription_elements('unlink').get_count()
        if total > 0:
            manual = _is_job_manual('unlink_expired_subscription_elements')
            printer("Expired subscriptions elements:", total)
            data = safe_db_execute('unlink_expired_subscription_elements', 'tasks.schedule', printer=printer,
                                   try_func=(lambda data: unlink_expired_subscription_elements(manual)))
            printer("Unlinked subscription elements:", data)
        else:
            printer("No subscriptions elements to process.")

    _execute_scheduled_task(_task, 'unlink_expired_subscription_elements', True, True)


@SCHEDULER.task('interval', **JOB_CONFIG['delete_expired_subscription_elements']['config'])
def delete_expired_subscription_elements_task():
    def _task(printer):
        total = expired_subscription_elements('delete').get_count()
        if total > 0:
            manual = _is_job_manual('delete_expired_subscription_elements')
            printer("Expired subscriptions elements:", total)
            data = safe_db_execute('delete_expired_subscription_elements', 'tasks.schedule', printer=printer,
                                   try_func=(lambda data: delete_expired_subscription_elements(manual)))
            printer("Deleted subscription elements:", data)
        else:
            printer("No subscriptions elements to process.")

    _execute_scheduled_task(_task, 'delete_expired_subscription_elements', True, True)


@SCHEDULER.task('interval', **JOB_CONFIG['archive_expired_subscription_elements']['config'])
def archive_expired_subscription_elements_task():
    def _task(printer):
        total = expired_subscription_elements('archive').get_count()
        if total > 0:
            manual = _is_job_manual('archive_expired_subscription_elements')
            printer("Expired subscriptions elements:", total)
            data = safe_db_execute('archive_expired_subscription_elements', 'tasks.schedule', printer=printer,
                                   try_func=(lambda data: archive_expired_subscription_elements(manual)))
            printer("Archived subscription elements:", data)
        else:
            printer("No subscriptions elements to process.")

    _execute_scheduled_task(_task, 'archive_expired_subscription_elements', True, True)


@SCHEDULER.task("interval", **JOB_CONFIG['relocate_old_posts']['config'])
def relocate_old_posts_task():
    def _task(printer):
        manual = _is_job_manual('relocate_old_posts')
        start = time.time()
        posts_moved = relocate_old_posts_to_alternate(manual)
        if posts_moved is None:
            printer("Alternate move days not configured.")
        else:
            printer("Posts moved:", posts_moved)
        printer("Task duration:", time.time() - start)

    if ALTERNATE_MEDIA_DIRECTORY is None:
        print("Alternate media directory not configured.")
    elif not os.path.exists(ALTERNATE_MEDIA_DIRECTORY):
        print("Alternate media directory not found.")
    else:
        _execute_scheduled_task(_task, 'relocate_old_posts', True, True)


@SCHEDULER.task("interval", **JOB_CONFIG['delete_orphan_images']['config'])
def delete_orphan_images_task():
    def _task(printer):
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

    _execute_scheduled_task(_task, 'delete_orphan_images', True, True)


@SCHEDULER.task('interval', **JOB_CONFIG['vacuum_analyze_database']['config'])
def vacuum_analyze_database_task():
    def _task(*args):
        with DB.engine.begin() as connection:
            connection.execute("VACUUM")
            connection.execute("ANALYZE")

    if not _is_job_manual('vacuum_analyze_database') and server_is_busy():
        print("Vaccuum/Analyze: Server busy, rescheduling....")
        reschedule_from_child('vacuum_analyze_database')
    else:
        _execute_scheduled_task(_task, 'vacuum_analyze_database', True, True)


# #### Startup tasks

@SCHEDULER.task('date', id="reset_subscription_status", next_run_time=seconds_from_now_local(60))
def reset_subscription_status_task():
    def _task(printer):
        subscriptions = get_busy_subscriptions()
        for subscription in subscriptions:
            update_subscription_status(subscription, 'idle')
        printer("Subscriptions reset:", len(subscriptions))
        update_subscriptions_ready(True)
        SESSION.commit()

    _execute_scheduled_task(_task, 'reset_subscription_status', False, False)


# #### Private

# ###### Semaphore

def _execute_scheduled_task(func, id, has_enabled, has_lock):
    display_name = ' '.join(word.title() for word in id.split('_'))
    if has_enabled and not _is_job_enabled(id):
        print(f"Task scheduler - {display_name}: disabled")
        return
    if has_lock and not _set_db_semaphore(id):
        print(f"Task scheduler - {display_name}: already running")
        return
    printer = buffered_print(display_name)
    printer("PID:", os.getpid())
    start_time = time.time()
    func(printer)
    printer("Execution time: %0.2f" % (time.time() - start_time))
    printer.print()
    if has_lock:
        _free_db_semaphore(id)
    SESSION.remove()


def _is_job_enabled(id):
    item = get_job_item('job_enable', id)
    return item.enabled if item is not None else False


def _is_job_manual(id):
    item = get_job_item('job_manual', id)
    return item.manual if item is not None else False


def _set_db_semaphore(id):
    item = get_job_item('job_lock', id)
    if item is None or item.locked:
        return False
    update_job_item(item, True)
    update_last_activity('server')
    SESSION.commit()
    return True


def _free_db_semaphore(id):
    update_job_by_id('job_lock', id, {'locked': False})
    SESSION.commit()


def _subscriptions_check():
    if not get_subscriptions_ready():
        print("Task scheduler - Subscription reset not yet initiated.")
        SESSION.remove()
        return False
    return True


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
        if error is None and subscription.status.name != 'error':
            update_subscription_status(subscription, 'idle')

    update_subscription_status(subscription, 'automatic')
    safe_db_execute('check_pending_subscriptions', 'tasks.schedule', scope_vars={'subscription': subscription},
                    try_func=try_func, msg_func=msg_func, error_func=error_func, finally_func=finally_func,
                    printer=printer)


def _pending_subscription_callback(subscription_ids):
    print_info('pending_subscription_callback', subscription_ids)
    subscriptions = get_subscription_by_ids(subscription_ids)
    for subscription in subscriptions:
        if subscription.status.name == 'automatic':
            update_subscription_status(subscription, 'idle')
    SESSION.remove()
