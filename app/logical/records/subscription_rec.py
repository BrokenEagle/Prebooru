# APP/LOGICAL/RECORDS/SUBSCRIPTION_REC.PY

# ## PYTHON IMPORTS
import threading

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import selectinload

# ## PACKAGE IMPORTS
from config import POPULATE_ELEMENTS_PER_PAGE, SYNC_MISSING_ILLUSTS_PER_PAGE, DOWNLOAD_POSTS_PER_PAGE,\
    UNLINK_ELEMENTS_PER_PAGE, DELETE_ELEMENTS_PER_PAGE, ARCHIVE_ELEMENTS_PER_PAGE,\
    DOWNLOAD_POSTS_PAGE_LIMIT, EXPIRE_ELEMENTS_PAGE_LIMIT
from utility.time import days_from_now, hours_from_now, days_ago, get_current_time
from utility.uprint import buffered_print, print_info

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Subscription, SubscriptionElement, Illust, IllustUrl, MediaAsset
from ..utility import SessionThread, SessionTimer
from ..searchable import search_attributes
from ..media import convert_mp4_to_webp
from ..logger import log_error
from ..downloader.network_dl import convert_network_subscription
from ..database.subscription_element_db import create_subscription_element_from_parameters,\
    update_subscription_element_from_parameters, link_subscription_post, pending_subscription_downloads_query,\
    unlink_subscription_post, delete_subscription_post, archive_subscription_post, expired_subscription_elements
from ..database.post_db import get_post_by_md5, get_posts_by_id
from ..database.illust_db import create_illust_from_parameters, update_illust_from_parameters, get_site_illust
from ..database.archive_db import get_archive
from ..database.error_db import is_error
from ..database.jobs_db import get_job_status_data, update_job_status, update_job_by_id
from ..database.subscription_db import add_subscription_error, update_subscription_from_parameters,\
    check_processing_subscriptions
from ..database.base_db import safe_db_execute
from .post_rec import recreate_archived_post
from .artist_rec import update_artist
from .image_hash_rec import generate_post_image_hashes


# ## GLOBAL VARIABLES

IMAGEMATCH_SEMAPHORE = threading.Semaphore(2)
VIDEO_SEMAPHORE = threading.Semaphore(1)

WAITING_THREADS = {
    'image_match': 0,
    'video': 0,
}


# ## FUNCTIONS

# #### Primary task functions

def process_subscription_manual(subscription_id, job_id, params):
    printer = buffered_print("Process Subscription")
    subscription = None
    start_illusts = 0
    start_posts = 0
    start_elements = 0
    starting_post_ids = []

    def try_func(scope_vars):
        nonlocal subscription, start_illusts, start_posts, start_elements, starting_post_ids
        subscription = Subscription.find(subscription_id)
        start_illusts = subscription.artist.illust_count
        start_posts = subscription.artist.post_count
        start_elements = subscription.element_count
        starting_post_ids = [post.id for post in subscription.posts]
        update_job_by_id('job_lock', job_id, {'locked': True})
        SESSION.commit()
        sync_missing_subscription_illusts(subscription, job_id, params)
        populate_subscription_elements(subscription, job_id)
        download_subscription_elements(subscription, job_id)
        job_status = get_job_status_data(job_id)
        job_status['stage'] = 'done'
        job_status['range'] = None
        update_job_status(job_id, job_status)

    def msg_func(scope_vars, e):
        return f"Unhandled exception occurred on subscripton pool #{subscription_id}: {repr(e)}"

    def error_func(scope_vars, e):
        nonlocal subscription
        subscription = subscription or Subscription.find(subscription_id)
        update_subscription_from_parameters(subscription, {'status': 'error'})

    def finally_func(scope_vars, error, data):
        nonlocal subscription
        subscription = subscription or Subscription.find(subscription_id)
        if error is None and subscription.status.name != 'error':
            update_subscription_from_parameters(subscription, {'status': 'idle'})
        SessionTimer(15, _query_unlock).start()  # Check later to give the DB time to catch up

    def _query_unlock():
        if not check_processing_subscriptions():
            update_job_by_id('job_lock', 'process_subscription_manual', {'locked': False})
            SESSION.commit()

    safe_db_execute('process_subscription_manual', 'records.subscription_rec',
                    try_func=try_func, msg_func=msg_func, printer=printer,
                    error_func=error_func, finally_func=finally_func)
    printer("Added illusts:", subscription.artist.illust_count - start_illusts)
    printer("Added posts:", subscription.artist.post_count - start_posts)
    printer("Added elements:", subscription.element_count - start_elements)
    printer.print()
    SESSION.remove()


def sync_missing_subscription_illusts(subscription, job_id=None, params=None):
    update_subscription_from_parameters(subscription, {'requery': hours_from_now(4)})
    artist = subscription.artist
    source = artist.site.source
    site_illust_ids = source.populate_all_artist_illusts(artist, job_id, params)
    if is_error(site_illust_ids):
        add_subscription_error(subscription, site_illust_ids)
        return
    if artist.updated < days_ago(1):
        params = source.get_artist_data(artist.site_artist_id)
        update_artist(artist, params)
    site_illust_ids = sorted(x for x in set(site_illust_ids))
    job_status = get_job_status_data(job_id) or {'illusts': 0}
    job_status['stage'] = 'illusts'
    job_status['records'] = len(site_illust_ids)
    print(f"sync_missing_subscription_illusts [{subscription.id}]: Total({len(site_illust_ids)})")
    for (i, item_id) in enumerate(site_illust_ids):
        if (i % SYNC_MISSING_ILLUSTS_PER_PAGE) == 0:
            total = len(site_illust_ids)
            first = i
            last = min(i + SYNC_MISSING_ILLUSTS_PER_PAGE, total)
            job_status['range'] = f"({first} - {last}) / {total}"
            update_job_status(job_id, job_status)
        data_params = source.get_illust_data(item_id)
        illust = get_site_illust(item_id, artist.site_id)
        if illust is None:
            data_params['artist_id'] = artist.id
            create_illust_from_parameters(data_params)
        else:
            update_illust_from_parameters(illust, data_params)
        job_status['illusts'] += 1
    job_status['ids'] = None
    update_job_status(job_id, job_status)
    update_subscription_from_parameters(subscription, {'requery': hours_from_now(subscription.interval),
                                                       'checked': get_current_time()})


def download_subscription_elements(subscription, job_id=None):
    job_status = get_job_status_data(job_id) or {'downloads': 0}
    job_status['stage'] = 'downloads'
    q = SubscriptionElement.query.enum_join(SubscriptionElement.status_enum)\
                                 .filter(SubscriptionElement.subscription_id == subscription.id,
                                         SubscriptionElement.post_id.is_(None),
                                         SubscriptionElement.status_filter('name', '__eq__', 'active'))
    q = q.options(selectinload(SubscriptionElement.illust_url).selectinload(IllustUrl.illust).lazyload('*'))
    q = q.order_by(SubscriptionElement.id.asc())
    page = q.limit_paginate(per_page=DOWNLOAD_POSTS_PER_PAGE)
    while True:
        print(f"download_subscription_elements: {page.first} - {page.last} / Total({page.count})")
        job_status['range'] = f"({page.first} - {page.last}) / {page.count}"
        update_job_status(job_id, job_status)
        for element in page.items:
            if convert_network_subscription(element):
                job_status['downloads'] += 1
        active_elements = [element for element in page.items if element.status.name == 'active']
        _process_image_matches(active_elements)
        _process_videos(active_elements)
        if not page.has_prev:
            break
        page = page.prev()
    update_job_status(job_id, job_status)


def download_missing_elements(manual=False):
    max_pages = DOWNLOAD_POSTS_PAGE_LIMIT if not manual else float('inf')
    q = pending_subscription_downloads_query()
    q = q.options(selectinload(SubscriptionElement.illust_url).selectinload(IllustUrl.illust).lazyload('*'))
    q = q.order_by(SubscriptionElement.id.asc())
    page = q.limit_paginate(per_page=DOWNLOAD_POSTS_PER_PAGE)
    element_count = 0
    while True:
        print(f"download_missing_elements: {page.first} - {page.last} / Total({page.count})")
        for element in page.items:
            convert_network_subscription(element)
            element_count += 1
        _process_image_matches(page.items)
        _process_videos(page.items)
        if not page.has_next or page.page >= max_pages:
            return element_count
        page = page.prev()


def unlink_expired_subscription_elements(manual):
    unlinked_elements = []
    max_pages = EXPIRE_ELEMENTS_PAGE_LIMIT if not manual else float('inf')
    q = expired_subscription_elements('unlink')
    q = q.order_by(SubscriptionElement.id.desc())
    page = q.limit_paginate(per_page=UNLINK_ELEMENTS_PER_PAGE)
    while True:
        print(f"\nunlink_expired_subscription_elements: {page.first} - {page.last} / Total({page.count})\n")
        for element in page.items:
            print(f"Unlinking {element.shortlink}")
            unlink_subscription_post(element)
            unlinked_elements.append(element.id)
        if not page.has_next or page.page >= max_pages:
            break
        page = page.next()
    return unlinked_elements


def delete_expired_subscription_elements(manual):
    deleted_elements = []
    max_pages = EXPIRE_ELEMENTS_PAGE_LIMIT if not manual else float('inf')
    q = expired_subscription_elements('delete')
    q = q.order_by(SubscriptionElement.id.desc())
    page = q.limit_paginate(per_page=DELETE_ELEMENTS_PER_PAGE)
    while True:
        print(f"\ndelete_expired_subscription_elements: {page.first} - {page.last} / Total({page.count})\n")
        for element in page.items:
            if element.media.has_file_access:
                print(f"Deleting post of {element.shortlink}")
                delete_subscription_post(element)
                deleted_elements.append(element.id)
        if not page.has_next or page.page >= max_pages:
            break
        page = page.next()
    return deleted_elements


def archive_expired_subscription_elements(manual):
    archived_elements = []
    max_pages = EXPIRE_ELEMENTS_PAGE_LIMIT if not manual else float('inf')
    q = expired_subscription_elements('archive')
    q = q.order_by(SubscriptionElement.id.desc())
    page = q.limit_paginate(per_page=ARCHIVE_ELEMENTS_PER_PAGE)
    while True:
        print(f"\nexpire_subscription_elements-archive: {page.first} - {page.last} / Total({page.count})\n")
        for element in page.items:
            if archive_subscription_post(element):
                print(f"Archiving post of {element.shortlink}")
                archived_elements.append(element.id)
        if not page.has_next or page.page >= max_pages:
            break
        page = page.next()
    return archived_elements


def populate_subscription_elements(subscription, job_id=None):
    job_status = get_job_status_data(job_id) or {'elements': 0}
    q = IllustUrl.query.join(Illust).filter(Illust.artist_id == subscription.artist_id)
    q = search_attributes(q, IllustUrl, {'post_exists': 'false', 'subscription_element_exists': 'false'})
    q = q.order_by(Illust.site_illust_id.asc(), IllustUrl.order.asc())
    total = q.get_count()
    page = 1
    job_status['stage'] = 'elements'
    while True:
        page_items = q.limit(POPULATE_ELEMENTS_PER_PAGE).all()
        if len(page_items) == 0:
            break
        page_border = (page - 1) * POPULATE_ELEMENTS_PER_PAGE
        first = min(1, len(page_items)) + page_border
        last = page_border + len(page_items)
        job_status['range'] = f"({first} - {last}) / {total}"
        print('populate_subscription_elements:', job_status['range'])
        update_job_status(job_id, job_status)
        for illust_url in page_items:
            createparams = {
                'subscription_id': subscription.id,
                'illust_url_id': illust_url.id,
                'expires': days_from_now(subscription.expiration) if subscription.expiration else None
            }
            create_subscription_element_from_parameters(createparams)
            job_status['elements'] += 1
        page += 1
    update_job_status(job_id, job_status)


def redownload_element(element):
    def try_func(scope_vars):
        nonlocal element
        initial_errors = [error.id for error in element.errors]
        if convert_network_subscription(element) and element.post_id is not None:
            update_subscription_element_from_parameters(element, {'status': 'active'})
            if element.post.is_video:
                SessionThread(target=convert_mp4_to_webp,
                              args=(element.post.file_path, element.post.video_preview_path)).start()
            return {'error': False}
        elif element.status.name == 'duplicate':
            post = element.illust_url.post
            if post is None:
                duplicate_string = '; '.join([dupelement.shortlink for dupelement in element.duplicate_elements])
                msg = "Duplicate of previous elements: " + duplicate_string
            else:
                msg = f'Duplicate of {element.illust_url.post.shortlink}'
            return {'error': True, 'message': msg}
        else:
            update_subscription_element_from_parameters(element, {'status': 'error', 'keep': 'unknown'})
            new_errors = [error for error in element.errors if error.id not in initial_errors]
            msg = '; '.join(f"{error.module}: {error.message}" for error in new_errors) or "Unknown error."
            return {'error': True, 'message': msg}

    def msg_func(scope_vars, error):
        return f"Unhandled exception occurred on subscripton #{element.subscription_id}: {repr(error)}"

    results = safe_db_execute('redownload_element', 'records.subscription_rec', try_func=try_func, msg_func=msg_func,
                              printer=print)
    return results


def reinstantiate_element(element):
    archive = get_archive('post', element.md5)
    if archive is None:
        if get_post_by_md5(element.md5) is not None:
            update_subscription_element_from_parameters(element, {'status': 'unlinked'})
        else:
            update_subscription_element_from_parameters(element, {'status': 'deleted'})
        return {'error': True, 'message': f'Post archive with MD5 {element.md5} does not exist.'}
    results = recreate_archived_post(archive, False)
    if results['error']:
        unlinked = SubscriptionElement.query.join(MediaAsset)\
                                            .filter(SubscriptionElement.md5 == element.md5,
                                                    SubscriptionElement.id.is_not(element.id),
                                                    SubscriptionElement.status_filter('name', '__eq__', 'unlinked'))\
                                            .first()
        if unlinked is not None:
            update_subscription_element_from_parameters(element, {'status': 'duplicate', 'keep': 'unknown'})
        return results
    relink_element(element)
    return {'error': False}


def relink_element(element):
    post = get_post_by_md5(element.md5)
    if post is None:
        if get_archive('post', element.md5) is not None:
            update_subscription_element_from_parameters(element, {'status': 'archived'})
        else:
            update_subscription_element_from_parameters(element, {'status': 'deleted'})
        return {'error': True, 'message': f'Post with MD5 {element.md5} does not exist.'}
    link_subscription_post(element, post)
    return {'error': False}


def subscription_slots_needed_per_hour():
    """The number of subscriptions that need to run every hour to keep up to date (assumes active all day)."""
    status_filter = Subscription.status_filter('name', 'in_', ['manual', 'automatic', 'idle'])
    subscriptions = Subscription.query.filter(status_filter).with_entities(Subscription.interval).all()
    return sum(1 / subscription.interval for subscription in subscriptions)


# #### Private

def _process_image_matches(elements):

    def _process(post_ids):
        print("Image match semaphore waits: %d" % WAITING_THREADS['image_match'])
        WAITING_THREADS['image_match'] += 1
        IMAGEMATCH_SEMAPHORE.acquire()
        WAITING_THREADS['image_match'] -= 1
        try:
            posts = get_posts_by_id(post_ids)
            for post in posts:
                generate_post_image_hashes(post)
                SESSION.commit()
        except Exception as e:
            msg = "Error processing image matches on subscription: %s" % str(e)
            log_error('subscription_rec._process_image_matches', msg)
            SESSION.rollback()
        finally:
            IMAGEMATCH_SEMAPHORE.release()

    post_ids = [element.post_id for element in elements]
    SessionThread(target=_process, args=(post_ids,)).start()


def _process_videos(elements):
    def _process(post_ids):
        printer = buffered_print(f"Process Videos [{thread.ident}]")
        print_info("Video semaphore wait:", WAITING_THREADS['video'])
        WAITING_THREADS['video'] += 1
        VIDEO_SEMAPHORE.acquire()
        WAITING_THREADS['video'] -= 1
        print_info("Video semaphore acquire:", WAITING_THREADS['video'])
        video_posts = get_posts_by_id(post_ids)
        mp4_count = 0
        try:
            for post in video_posts:
                if post.file_ext == 'mp4':
                    convert_mp4_to_webp(post.file_path, post.video_preview_path)
                    mp4_count += 1
        except Exception as e:
            msg = "Error processing videos on subscription: %s" % str(e)
            log_error('subscription_rec.process_videos', msg)
        finally:
            VIDEO_SEMAPHORE.release()
            print_info("Video semaphore release:", WAITING_THREADS['video'])
        printer("Videos processed:", {'mp4': mp4_count})

    posts = [element.post for element in elements if element.post is not None]
    video_posts = [post for post in posts if post.media.is_video]
    if len(video_posts):
        post_ids = [post.id for post in video_posts]
        thread = SessionThread(target=_process, args=(post_ids,))
        thread.start()
