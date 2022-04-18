# APP/LOGICAL/CHECK/SUBSCRIPTIONS.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import selectinload

# ## PACKAGE IMPORTS
from utility.time import hours_from_now

# ## LOCAL IMPORTS
from ...models import SubscriptionPoolElement, IllustUrl
from ..sites import get_site_key
from ..sources import SOURCEDICT
from ..database.illust_db import create_illust_from_parameters, update_illust_from_parameters
from ..database.subscription_pool_db import update_subscription_pool_requery, update_subscription_pool_last_info,\
    add_subscription_pool_error
from ..database.error_db import is_error
from ..records.subscription_rec import update_subscription_elements
from ..downloader.network import convert_network_subscription


# ## FUNCTIONS

def download_subscription_illusts(subscription_pool):
    update_subscription_pool_requery(subscription_pool, hours_from_now(1))
    artist = subscription_pool.artist
    site_key = get_site_key(artist.site_id)
    source = SOURCEDICT[site_key]
    site_illust_ids = source.populate_all_artist_illusts(artist, subscription_pool.last_id)
    if is_error(site_illust_ids):
        add_subscription_pool_error(subscription_pool, site_illust_ids)
        return
    print(f"download_subscription_illusts [{subscription_pool.id}]: Total({len(site_illust_ids)})")
    for (i, item_id) in enumerate(site_illust_ids):
        if (i % 20) == 0:
            total = len(site_illust_ids)
            first = i
            last = min(i + 20, total)
        data_params = source.get_illust_data(item_id)
        illust = source.get_site_illust(item_id, artist.site_id)
        if illust is None:
            data_params['artist_id'] = artist.id
            create_illust_from_parameters(data_params)
        else:
            update_illust_from_parameters(illust, data_params)
    last_id = max(site_illust_ids) if len(site_illust_ids) else subscription_pool.last_id
    update_subscription_pool_last_info(subscription_pool, last_id)
    update_subscription_pool_requery(subscription_pool, hours_from_now(subscription_pool.interval))
    update_subscription_elements(subscription_pool)


def download_subscription_elements(subscription_pool):
    site_key = get_site_key(subscription_pool.artist.site_id)
    source = SOURCEDICT[site_key]
    q = SubscriptionPoolElement.query.filter_by(pool_id=subscription_pool.id, post_id=None, active=True)
    q = q.options(selectinload(SubscriptionPoolElement.illust_url).selectinload(IllustUrl.illust).lazyload('*'))
    page = q.limit_paginate(per_page=5)
    while True:
        print(f"download_subscription_elements: {page.first} - {page.last} / Total({page.count})")
        for element in page.items:
            convert_network_subscription(element, source)
        if not page.has_next:
            break
        page = page.next()
