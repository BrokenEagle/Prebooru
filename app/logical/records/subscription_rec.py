# APP/LOGICAL/RECORDS/SUBSCRIPTION_REC.PY

# ## PACKAGE IMPORTS
from utility.time import days_from_now

# ## LOCAL IMPORTS
from ...models import Illust, IllustUrl
from ..searchable import search_attributes
from ..sites import get_site_key
from ..sources import SOURCEDICT
from ..downloader.network import convert_network_subscription
from ..database.subscription_pool_element_db import create_subscription_pool_element_from_parameters,\
    update_subscription_pool_element_deleted, update_subscription_pool_element_status
from ..database.jobs_db import get_job_status_data, update_job_status
from ..database.base_db import safe_db_execute


# ## GLOBAL VARIABLES

ILLUST_URL_PAGE_LIMIT = 50


# ## FUNCTIONS

def update_subscription_elements(subscription_pool, job_id=None):
    job_status = get_job_status_data(job_id) or {'elements': 0}
    q = IllustUrl.query.join(Illust).filter(Illust.artist_id == subscription_pool.artist_id)
    q = search_attributes(q, IllustUrl, {'has_post': 'false', 'subscription_pool_element_exists': 'false'})
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
                'pool_id': subscription_pool.id,
                'illust_url_id': illust_url.id,
                'expires': days_from_now(subscription_pool.expiration) if subscription_pool.expiration else None
            }
            create_subscription_pool_element_from_parameters(createparams)
            job_status['elements'] += 1
    update_job_status(job_id, job_status)


def redownload_element(element):
    site_key = get_site_key(element.pool.artist.site_id)
    source = SOURCEDICT[site_key]

    def try_func(scope_vars):
        nonlocal element, source
        update_subscription_pool_element_deleted(element, False)
        if convert_network_subscription(element, source):
            update_subscription_pool_element_status(element, 'active')
            return True
        else:
            return False

    def msg_func(scope_vars, error):
        return f"Unhandled exception occurred on subscripton pool #{element.pool_id}: {repr(error)}"

    def error_func(scope_vars, error):
        update_subscription_pool_element_deleted(element, True)

    return safe_db_execute('redownload_element', 'records.subscription_rec', try_func=try_func, msg_func=msg_func,
                           error_func=error_func, printer=print)
