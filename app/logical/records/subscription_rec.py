# APP/LOGICAL/RECORDS/SUBSCRIPTION_REC.PY

# ## PYTHON IMPORTS
import threading

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import selectinload

# ## PACKAGE IMPORTS
from utility.time import days_from_now, hours_from_now
from utility.uprint import buffered_print, print_info

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Subscription, SubscriptionElement, Illust, IllustUrl
from ..utility import SessionThread, SessionTimer
from ..searchable import search_attributes
from ..media import convert_mp4_to_webp
from ..logger import log_error
from ..downloader.network import convert_network_subscription
from ..records.post_rec import reinstantiate_archived_post
from ..database.subscription_element_db import create_subscription_element_from_parameters,\
    update_subscription_element_status, link_subscription_post
from ..database.post_db import get_post_by_md5, get_posts_by_id
from ..database.illust_db import create_illust_from_parameters, update_illust_from_parameters
from ..database.archive_db import get_archive
from ..database.error_db import is_error
from ..database.jobs_db import get_job_status_data, update_job_status, update_job_by_id
from ..database.subscription_element_db import unlink_subscription_post, delete_subscription_post,\
    archive_subscription_post, expired_subscription_elements
from ..database.subscription_db import update_subscription_requery, update_subscription_last_info,\
    add_subscription_error, update_subscription_status, update_subscription_active, check_processing_subscriptions
from ..database.base_db import safe_db_execute
from .image_hash_rec import generate_post_image_hashes


# ## GLOBAL VARIABLES

ILLUST_URL_PAGE_LIMIT = 50
ILLUST_PAGE_LIMIT = 10
POST_PAGE_LIMIT = 5
DOWNLOAD_PAGE_LIMIT = 10
EXPIRE_PAGE_LIMIT = 20

IMAGEMATCH_SEMAPHORE = threading.Semaphore(2)
VIDEO_SEMAPHORE = threading.Semaphore(1)

WAITING_THREADS = {
    'image_match': 0,
    'video': 0,
}


# ## FUNCTIONS

# #### Primary task functions

def process_subscription(subscription_id, job_id):
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
        update_job_by_id('job_lock', 'process_subscription', {'locked': True})
        SESSION.commit()
        download_subscription_illusts(subscription, job_id)
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
        update_subscription_status(subscription, 'error')
        update_subscription_active(subscription, False)

    def finally_func(scope_vars, error, data):
        nonlocal subscription
        subscription = subscription or Subscription.find(subscription_id)
        if error is None and subscription.status.name != 'error':
            update_subscription_status(subscription, 'idle')
        SessionTimer(15, _query_unlock).start()  # Check later to give the DB time to catch up

    def _query_unlock():
        if not check_processing_subscriptions():
            update_job_by_id('job_lock', 'process_subscription', {'locked': False})
            SESSION.commit()

    safe_db_execute('process_subscription', 'records.subscription_rec',
                    try_func=try_func, msg_func=msg_func, printer=printer,
                    error_func=error_func, finally_func=finally_func)
    printer("Added illusts:", subscription.artist.illust_count - start_illusts)
    printer("Added posts:", subscription.artist.post_count - start_posts)
    printer("Added elements:", subscription.element_count - start_elements)
    printer.print()
    SESSION.remove()


def download_subscription_illusts(subscription, job_id=None):
    update_subscription_requery(subscription, hours_from_now(4))
    artist = subscription.artist
    source = artist.site_id.source
    site_illust_ids = source.populate_all_artist_illusts(artist, subscription.last_id, job_id)
    if is_error(site_illust_ids):
        add_subscription_error(subscription, site_illust_ids)
        return
    site_illust_ids = sorted(x for x in set(site_illust_ids))
    job_status = get_job_status_data(job_id) or {'illusts': 0}
    job_status['stage'] = 'illusts'
    job_status['records'] = len(site_illust_ids)
    print(f"download_subscription_illusts [{subscription.id}]: Total({len(site_illust_ids)})")
    for (i, item_id) in enumerate(site_illust_ids):
        if (i % ILLUST_PAGE_LIMIT) == 0:
            total = len(site_illust_ids)
            first = i
            last = min(i + ILLUST_PAGE_LIMIT, total)
            job_status['range'] = f"({first} - {last}) / {total}"
            update_job_status(job_id, job_status)
        data_params = source.get_illust_data(item_id)
        illust = source.get_site_illust(item_id, artist.site_id.value)
        if illust is None:
            data_params['artist_id'] = artist.id
            create_illust_from_parameters(data_params)
        else:
            update_illust_from_parameters(illust, data_params)
        job_status['illusts'] += 1
    update_job_status(job_id, job_status)
    if len(site_illust_ids):
        update_subscription_last_info(subscription, max(site_illust_ids))
    update_subscription_requery(subscription, hours_from_now(subscription.interval))
    update_subscription_elements(subscription, job_id)


def download_subscription_elements(subscription, job_id=None):
    job_status = get_job_status_data(job_id) or {'downloads': 0}
    job_status['stage'] = 'downloads'
    q = SubscriptionElement.query.filter_by(subscription_id=subscription.id, post_id=None, status='active')
    q = q.options(selectinload(SubscriptionElement.illust_url).selectinload(IllustUrl.illust).lazyload('*'))
    q = q.order_by(SubscriptionElement.id.asc())
    page = q.limit_paginate(per_page=POST_PAGE_LIMIT)
    while True:
        print(f"download_subscription_elements: {page.first} - {page.last} / Total({page.count})")
        job_status['range'] = f"({page.first} - {page.last}) / {page.count}"
        update_job_status(job_id, job_status)
        for element in page.items:
            if convert_network_subscription(element):
                job_status['downloads'] += 1
        _process_image_matches(page.items)
        _process_videos(page.items)
        if not page.has_prev:
            break
        page = page.prev()
    update_job_status(job_id, job_status)


def download_missing_elements(manual=False):
    max_pages = DOWNLOAD_PAGE_LIMIT if not manual else float('inf')
    q = SubscriptionElement.query.join(Subscription)\
                                 .filter(SubscriptionElement.post_id.is_(None),
                                         SubscriptionElement.status == 'active',
                                         Subscription.status == 'idle')
    q = q.options(selectinload(SubscriptionElement.illust_url).selectinload(IllustUrl.illust).lazyload('*'))
    q = q.order_by(SubscriptionElement.id.asc())
    page = q.limit_paginate(per_page=POST_PAGE_LIMIT)
    element_count = 0
    while True:
        print(f"download_missing_elements: {page.first} - {page.last} / Total({page.count})")
        for element in page.items:
            convert_network_subscription(element)
            element_count += 1
        _process_image_matches(page.items)
        _process_videos(page.items)
        if not page.has_prev or (not manual and max_pages):
            return element_count
        page = page.prev()


def unlink_expired_subscription_elements(manual):
    unlink_count = 0
    max_pages = EXPIRE_PAGE_LIMIT if not manual else float('inf')
    q = expired_subscription_elements('unlink')
    q = q.order_by(SubscriptionElement.id.desc())
    page = q.limit_paginate(per_page=50)
    while True:
        print(f"\nunlink_expired_subscription_elements: {page.first} - {page.last} / Total({page.count})\n")
        for element in page.items:
            print(f"Unlinking {element.shortlink}")
            unlink_subscription_post(element)
            unlink_count += 1
        if not page.has_next or page.page >= max_pages:
            break
        page = page.next()
    return unlink_count


def delete_expired_subscription_elements(manual):
    delete_count = 0
    max_pages = EXPIRE_PAGE_LIMIT if not manual else float('inf')
    q = expired_subscription_elements('delete')
    q = q.order_by(SubscriptionElement.id.desc())
    page = q.limit_paginate(per_page=10)
    while True:
        print(f"\ndelete_expired_subscription_elements: {page.first} - {page.last} / Total({page.count})\n")
        for element in page.items:
            print(f"Deleting post of {element.shortlink}")
            delete_subscription_post(element)
            delete_count += 1
        if not page.has_next or page.page >= max_pages:
            break
        page = page.next()
    return delete_count


def archive_expired_subscription_elements(manual):
    archive_count = 0
    max_pages = EXPIRE_PAGE_LIMIT if not manual else float('inf')
    q = expired_subscription_elements('archive')
    q = q.order_by(SubscriptionElement.id.desc())
    page = q.limit_paginate(per_page=10)
    while True:
        print(f"\nexpire_subscription_elements-archive: {page.first} - {page.last} / Total({page.count})\n")
        for element in page.items:
            print(f"Archiving post of {element.shortlink}")
            archive_subscription_post(element)
            archive_count += 1
        if not page.has_next or page.page >= max_pages:
            break
        page = page.next()
    return archive_count


def update_subscription_elements(subscription, job_id=None):
    job_status = get_job_status_data(job_id) or {'elements': 0}
    q = IllustUrl.query.join(Illust).filter(Illust.artist_id == subscription.artist_id)
    q = search_attributes(q, IllustUrl, {'has_post': 'false', 'subscription_element_exists': 'false'})
    q = q.order_by(Illust.site_illust_id.asc(), IllustUrl.order.asc())
    total = q.get_count()
    page = 1
    job_status['stage'] = 'elements'
    while True:
        page_items = q.limit(ILLUST_URL_PAGE_LIMIT).all()
        if len(page_items) == 0:
            break
        page_border = (page - 1) * ILLUST_URL_PAGE_LIMIT
        first = min(1, len(page_items)) + page_border
        last = page_border + len(page_items)
        job_status['range'] = f"({first} - {last}) / {total}"
        print('update_subscription_elements:', job_status['range'])
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
        if convert_network_subscription(element):
            update_subscription_element_status(element, 'active')
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
            update_subscription_element_status(element, 'error')
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
            update_subscription_element_status(element, 'unlinked')
        else:
            update_subscription_element_status(element, 'deleted')
        return {'error': True, 'message': f'Post archive with MD5 {element.md5} does not exist.'}
    results = reinstantiate_archived_post(archive, False)
    if not results['error']:
        relink_element(element)
    return {'error': False}


def relink_element(element):
    post = get_post_by_md5(element.md5)
    if post is None:
        if get_archive('post', element.md5) is not None:
            update_subscription_element_status(element, 'archived')
        else:
            update_subscription_element_status(element, 'deleted')
        return {'error': True, 'message': f'Post with MD5 {element.md5} does not exist.'}
    link_subscription_post(element, post)
    return {'error': False}


# #### Private

def _process_image_matches(elements):

    def _process(post_ids):
        print("Image match semaphore waits:", WAITING_THREADS['image_match'])
        WAITING_THREADS['image_match'] += 1
        IMAGEMATCH_SEMAPHORE.acquire()
        WAITING_THREADS['image_match'] -= 1
        try:
            posts = get_posts_by_id(post_ids)
            for post in posts:
                generate_post_image_hashes(post)
        except Exception as e:
            msg = "Error processing image matches on subscription: %s" % str(e)
            log_error('subscription_rec._process_image_matches', msg)
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
    video_posts = [post for post in posts if post.is_video]
    if len(video_posts):
        post_ids = [post.id for post in video_posts]
        thread = SessionThread(target=_process, args=(post_ids,))
        thread.start()
