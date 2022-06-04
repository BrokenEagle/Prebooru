# APP/LOGICAL/CHECK/SUBSCRIPTIONS.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import selectinload

# ## PACKAGE IMPORTS
from utility.time import get_current_time, hours_from_now

# ## LOCAL IMPORTS
from ...models import SubscriptionPool, SubscriptionPoolElement, IllustUrl
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


# ## FUNCTIONS

def download_subscription_illusts(subscription_pool, job_id=None):
    update_subscription_pool_requery(subscription_pool, hours_from_now(1))
    artist = subscription_pool.artist
    site_key = get_site_key(artist.site_id)
    source = SOURCEDICT[site_key]
    site_illust_ids = source.populate_all_artist_illusts(artist, subscription_pool.last_id, job_id)
    if is_error(site_illust_ids):
        add_subscription_pool_error(subscription_pool, site_illust_ids)
        return
    job_status = get_job_status_data(job_id) or {'illust_creates': 0, 'illust_updates': 0}
    job_status['stage'] = 'illusts'
    job_status['records'] = len(site_illust_ids)
    print(f"download_subscription_illusts [{subscription_pool.id}]: Total({len(site_illust_ids)})")
    for (i, item_id) in enumerate(site_illust_ids):
        if (i % 20) == 0:
            total = len(site_illust_ids)
            first = i
            last = min(i + 20, total)
            job_status['range'] = f"({first} - {last}) / {total}"
            update_job_status(job_id, job_status)
        data_params = source.get_illust_data(item_id)
        illust = source.get_site_illust(item_id, artist.site_id)
        if illust is None:
            data_params['artist_id'] = artist.id
            create_illust_from_parameters(data_params)
            job_status['illust_creates'] += 1
        else:
            update_illust_from_parameters(illust, data_params)
            job_status['illust_updates'] += 1
    update_job_status(job_id, job_status)
    last_id = max(site_illust_ids) if len(site_illust_ids) else subscription_pool.last_id
    update_subscription_pool_last_info(subscription_pool, last_id)
    update_subscription_pool_requery(subscription_pool, hours_from_now(subscription_pool.interval))
    update_subscription_elements(subscription_pool, job_id)


def download_subscription_elements(subscription_pool, job_id=None):
    job_status = get_job_status_data(job_id) or {'downloads': 0}
    job_status['stage'] = 'downloads'
    site_key = get_site_key(subscription_pool.artist.site_id)
    source = SOURCEDICT[site_key]
    q = SubscriptionPoolElement.query.filter_by(pool_id=subscription_pool.id, post_id=None, active=True)
    q = q.options(selectinload(SubscriptionPoolElement.illust_url).selectinload(IllustUrl.illust).lazyload('*'))
    page = q.limit_paginate(per_page=5)
    while True:
        print(f"download_subscription_elements: {page.first} - {page.last} / Total({page.count})")
        job_status['range'] = f"({page.first} - {page.last}) / {page.count}"
        update_job_status(job_id, job_status)
        for element in page.items:
            if convert_network_subscription(element, source):
                job_status['downloads'] += 1
        if not page.has_next:
            break
        page = page.next()
    update_job_status(job_id, job_status)


def download_missing_elements():
    q = SubscriptionPoolElement.query.join(SubscriptionPool)\
                               .filter(SubscriptionPoolElement.post_id.is_(None),
                                       SubscriptionPoolElement.active.is_(True),
                                       SubscriptionPoolElement.deleted.is_(False),
                                       SubscriptionPool.status == 'idle')
    q = q.options(selectinload(SubscriptionPoolElement.illust_url).selectinload(IllustUrl.illust).lazyload('*'))
    page = q.limit_paginate()
    while True:
        print(f"download_subscription_elements: {page.first} - {page.last} / Total({page.count})")
        for element in page.items:
            site_key = get_site_key(element.illust_url.site_id)
            source = SOURCEDICT[site_key]
            convert_network_subscription(element, source)
        if not page.has_next:
            break
        if page.page > 10:
            print("download_missing_elements: Max pages reached!")
            break
        page = page.next()


def expire_subscription_elements():
    # First pass - Unlink all "yes" elements
    q = SubscriptionPoolElement.query.filter(SubscriptionPoolElement.expires < get_current_time(),
                                             SubscriptionPoolElement.keep == 'yes')
    page = q.limit_paginate(per_page=100)
    while True:
        print(f"expire_subscription_elements-unlink: {page.first} - {page.last} / Total({page.count})")
        for element in page.items:
            print(f"Unlinking {element.shortlink}")
            unlink_subscription_post(element)
        if not page.has_next:
            break
        page = page.next()
    # Second pass - Hard delete all "no" element posts
    q = SubscriptionPoolElement.query.filter(SubscriptionPoolElement.expires < get_current_time(),
                                             SubscriptionPoolElement.keep == 'no')
    page = q.limit_paginate(per_page=50)
    while True:
        print(f"expire_subscription_elements-delete: {page.first} - {page.last} / Total({page.count})")
        for element in page.items:
            print(f"Deleting post of {element.shortlink}")
            delete_subscription_post(element)
        if not page.has_next:
            break
        page = page.next()
    # Third pass - Soft delete (archive with ### expiration) all unchosen element posts
    q = SubscriptionPoolElement.query.filter(SubscriptionPoolElement.expires < get_current_time(),
                                             SubscriptionPoolElement.keep.is_(None))
    page = q.limit_paginate(per_page=50)
    while True:
        print(f"expire_subscription_elements-archive: {page.first} - {page.last} / Total({page.count})")
        for element in page.items:
            print(f"Archiving post of {element.shortlink}")
            archive_subscription_post(element)
        if not page.has_next:
            break
        page = page.next()
