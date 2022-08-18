# APP/LOGICAL/CHECK/SUBSCRIPTIONS.PY

# ## PYTHON IMPORTS
import threading

# ## EXTERNAL IMPORTS
from sqlalchemy import and_, or_
from sqlalchemy.orm import selectinload

# ## PACKAGE IMPORTS
from utility.time import get_current_time, hours_from_now

# ## LOCAL IMPORTS
from ...models import SubscriptionPool, SubscriptionPoolElement, IllustUrl, Post
from ..sites import get_site_key
from ..sources import SOURCEDICT
from ..database.illust_db import create_illust_from_parameters, update_illust_from_parameters
from ..database.subscription_pool_element_db import unlink_subscription_post, delete_subscription_post,\
    archive_subscription_post
from ..database.subscription_pool_db import update_subscription_pool_requery, update_subscription_pool_last_info,\
    add_subscription_pool_error
from ..database.error_db import is_error
from ..database.jobs_db import get_job_status_data, update_job_status
from ..records.subscription_rec import update_subscription_elements
from ..downloader.network import convert_network_subscription
from ..logger import log_error

# ## GLOBAL VARIABLES

ILLUST_PAGE_LIMIT = 10
POST_PAGE_LIMIT = 5
EXPIRE_PAGE_LIMIT = 10

SIMILARITY_SEMAPHORE = threading.Semaphore(2)
VIDEO_SEMAPHORE = threading.Semaphore(1)

WAITING_THREADS = {
    'similarity': 0,
    'video': 0,
    }

# ## FUNCTIONS

def download_subscription_illusts(subscription_pool, job_id=None):
    update_subscription_pool_requery(subscription_pool, hours_from_now(4))
    artist = subscription_pool.artist
    site_key = get_site_key(artist.site_id)
    source = SOURCEDICT[site_key]
    site_illust_ids = source.populate_all_artist_illusts(artist, subscription_pool.last_id, job_id)
    if is_error(site_illust_ids):
        add_subscription_pool_error(subscription_pool, site_illust_ids)
        return
    site_illust_ids = sorted(x for x in set(site_illust_ids))
    job_status = get_job_status_data(job_id) or {'illusts': 0}
    job_status['stage'] = 'illusts'
    job_status['records'] = len(site_illust_ids)
    print(f"download_subscription_illusts [{subscription_pool.id}]: Total({len(site_illust_ids)})")
    for (i, item_id) in enumerate(site_illust_ids):
        if (i % ILLUST_PAGE_LIMIT) == 0:
            total = len(site_illust_ids)
            first = i
            last = min(i + ILLUST_PAGE_LIMIT, total)
            job_status['range'] = f"({first} - {last}) / {total}"
            update_job_status(job_id, job_status)
        data_params = source.get_illust_data(item_id)
        illust = source.get_site_illust(item_id, artist.site_id)
        if illust is None:
            data_params['artist_id'] = artist.id
            create_illust_from_parameters(data_params)
        else:
            update_illust_from_parameters(illust, data_params)
        job_status['illusts'] += 1
    update_job_status(job_id, job_status)
    if len(site_illust_ids):
        update_subscription_pool_last_info(subscription_pool, max(site_illust_ids))
    update_subscription_pool_requery(subscription_pool, hours_from_now(subscription_pool.interval))
    update_subscription_elements(subscription_pool, job_id)


def download_subscription_elements(subscription_pool, job_id=None):
    job_status = get_job_status_data(job_id) or {'downloads': 0}
    job_status['stage'] = 'downloads'
    site_key = get_site_key(subscription_pool.artist.site_id)
    source = SOURCEDICT[site_key]
    q = SubscriptionPoolElement.query.filter_by(pool_id=subscription_pool.id, post_id=None, active=True)
    q = q.options(selectinload(SubscriptionPoolElement.illust_url).selectinload(IllustUrl.illust).lazyload('*'))
    q = q.order_by(SubscriptionPoolElement.id.asc())
    page = q.limit_paginate(per_page=POST_PAGE_LIMIT)
    while True:
        print(f"download_subscription_elements: {page.first} - {page.last} / Total({page.count})")
        job_status['range'] = f"({page.first} - {page.last}) / {page.count}"
        update_job_status(job_id, job_status)
        for element in page.items:
            if convert_network_subscription(element, source):
                job_status['downloads'] += 1
        _process_similarity(page.items)
        _process_videos(page.items)
        if not page.has_prev:
            break
        page = page.prev()
    update_job_status(job_id, job_status)


def download_missing_elements(manual=False):
    q = SubscriptionPoolElement.query.join(SubscriptionPool)\
                               .filter(SubscriptionPoolElement.post_id.is_(None),
                                       SubscriptionPoolElement.active.is_(True),
                                       SubscriptionPoolElement.deleted.is_(False),
                                       SubscriptionPool.status == 'idle')
    q = q.options(selectinload(SubscriptionPoolElement.illust_url).selectinload(IllustUrl.illust).lazyload('*'))
    q = q.order_by(SubscriptionPoolElement.id.asc())
    page = q.limit_paginate(per_page=POST_PAGE_LIMIT)
    while True:
        print(f"download_missing_elements: {page.first} - {page.last} / Total({page.count})")
        for element in page.items:
            site_key = get_site_key(element.illust_url.site_id)
            source = SOURCEDICT[site_key]
            convert_network_subscription(element, source)
        _process_similarity(page.items)
        _process_videos(page.items)
        if not page.has_prev:
            break
        if not manual and page.page > 10:
            print("download_missing_elements: Max pages reached!")
            break
        page = page.prev()


def expire_subscription_elements(manual):
    retdata = {'unlink': 0, 'delete': 0, 'archive': 0}
    max_pages = EXPIRE_PAGE_LIMIT if not manual else float('inf')
    # First pass - Unlink all "yes" elements or those that were manually downloaded by the user
    expired_clause = and_(SubscriptionPoolElement.expires < get_current_time(), SubscriptionPoolElement.keep == 'yes')
    user_clause = (Post.type == 'user_post')
    q = SubscriptionPoolElement.query.join(Post, SubscriptionPoolElement.post).filter(or_(expired_clause, user_clause))
    q = q.order_by(SubscriptionPoolElement.id.desc())
    page = q.limit_paginate(per_page=100)
    while True:
        print(f"\nexpire_subscription_elements-unlink: {page.first} - {page.last} / Total({page.count})\n")
        for element in page.items:
            print(f"Unlinking {element.shortlink}")
            unlink_subscription_post(element)
            retdata['unlink'] += 1
        if not page.has_next or page.page > max_pages:
            break
        page = page.next()
    # Second pass - Hard delete all "no" element posts
    q = SubscriptionPoolElement.query.filter(SubscriptionPoolElement.expires < get_current_time(),
                                             SubscriptionPoolElement.keep == 'no')
    q = q.order_by(SubscriptionPoolElement.id.desc())
    page = q.limit_paginate(per_page=25)
    while True:
        print(f"\nexpire_subscription_elements-delete: {page.first} - {page.last} / Total({page.count})\n")
        for element in page.items:
            print(f"Deleting post of {element.shortlink}")
            delete_subscription_post(element)
            retdata['delete'] += 1
        if not page.has_next or page.page > max_pages:
            break
        page = page.next()
    # Third pass - Soft delete (archive with ### expiration) all unchosen element posts
    q = SubscriptionPoolElement.query.filter(SubscriptionPoolElement.expires < get_current_time(),
                                             SubscriptionPoolElement.status == 'active',
                                             or_(SubscriptionPoolElement.keep == 'archive',
                                                 SubscriptionPoolElement.keep.is_(None)))
    q = q.order_by(SubscriptionPoolElement.id.desc())
    page = q.limit_paginate(per_page=25)
    while True:
        print(f"expire_subscription_elements-archive: {page.first} - {page.last} / Total({page.count})")
        for element in page.items:
            print(f"Archiving post of {element.shortlink}")
            archive_subscription_post(element)
            retdata['archive'] += 1
        if not page.has_next or page.page > max_pages:
            break
        page = page.next()


# #### Private

def _process_similarity(elements):
    from ..tasks.worker import process_similarity

    def _process(post_ids):
        print("Similarity semaphore waits:", WAITING_THREADS['similarity'])
        WAITING_THREADS['similarity'] += 1
        SIMILARITY_SEMAPHORE.acquire()
        WAITING_THREADS['similarity'] -= 1
        try:
            process_similarity(post_ids)
        except Exception as e:
            msg = "Error processing similarity on subscription: %s" % str(e)
            log_error('check.subscriptions.process_similarity', msg)
        finally:
            SIMILARITY_SEMAPHORE.release()

    post_ids = [element.post_id for element in elements]
    threading.Thread(target=_process, args=(post_ids,)).start()


def _process_videos(elements):
    from ..tasks.worker import process_videos

    def _process(post_ids):
        print("Video semaphore waits:", WAITING_THREADS['video'])
        WAITING_THREADS['video'] += 1
        VIDEO_SEMAPHORE.acquire()
        WAITING_THREADS['video'] -= 1
        try:
            process_videos(post_ids)
        except Exception as e:
            msg = "Error processing videos on subscription: %s" % str(e)
            log_error('check.subscriptions.process_videos', msg)
        finally:
            VIDEO_SEMAPHORE.release()

    posts = [element.post for element in elements if element.post is not None]
    video_post_ids = [post.id for post in posts if post.is_video]
    if len(video_post_ids):
        threading.Thread(target=_process, args=(video_post_ids,)).start()
