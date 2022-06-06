# APP/LOGICAL/RECORDS/SUBSCRIPTION_REC.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import selectinload

# ## PACKAGE IMPORTS
from utility.time import days_from_now

# ## LOCAL IMPORTS
from ...models import Illust, IllustUrl
from ..searchable import search_attributes
from ..sites import get_site_key
from ..sources import SOURCEDICT
from ..downloader.network import convert_network_subscription
from ..database.subscription_pool_element_db import create_subscription_pool_element_from_parameters,\
    update_subscription_pool_element_deleted
from ..database.jobs_db import get_job_status_data, update_job_status
from ..database.base_db import safe_db_execute


# ## FUNCTIONS

def update_subscription_elements(subscription_pool, job_id=None):
    job_status = get_job_status_data(job_id) or {'elements': 0}
    q = Illust.query.filter_by(artist_id=subscription_pool.artist_id)
    q = search_attributes(q, Illust, {'urls': {'has_post': 'false'}})
    q = q.options(
        selectinload(Illust.urls).options(
            selectinload(IllustUrl.post).lazyload('*'),
            selectinload(IllustUrl.subscription_pool_element).lazyload('*'),
        )
    )
    q = q.order_by(Illust.site_illust_id.asc())
    page = q.paginate(per_page=50)
    job_status['stage'] = 'elements'
    while True:
        print(f"update_subscription_elements: {page.first} - {page.last} / Total({page.total})")
        job_status['range'] = f"({page.first} - {page.last}) / {page.total}"
        update_job_status(job_id, job_status)
        for illust in page.items:
            if illust.type == 'image':
                illust_urls = sorted(illust.urls, key=lambda x: x.order)
            elif illust.type == 'video':
                illust_urls = [illust.video_illust_url]
            else:
                print("Unknown illust type: %s" % illust.shortlink)
                continue
            for illust_url in illust_urls:
                if illust_url.post is not None or illust_url.subscription_pool_element is not None:
                    continue
                createparams = {
                    'pool_id': subscription_pool.id,
                    'illust_url_id': illust_url.id,
                    'expires': days_from_now(subscription_pool.expiration) if subscription_pool.expiration else None
                }
                create_subscription_pool_element_from_parameters(createparams)
                job_status['elements'] += 1
        if not page.has_next:
            break
        page = page.next()
    update_job_status(job_id, job_status)


def redownload_element(element):
    site_key = get_site_key(element.pool.artist.site_id)
    source = SOURCEDICT[site_key]

    def try_func():
        nonlocal element, source
        if convert_network_subscription(element, source, True):
            flash('Element redownloaded.')
            update_subscription_pool_element_deleted(element, False)
        else:
            flash('Error downloading element.', 'error')

    def msg_func(scope_vars, error):
        return f"Unhandled exception occurred on subscripton pool #{subscription_id}: {repr(error)}"

    def error_func(scope_vars, error):
        flash(f"Unhandled exception occurred: {repr(error)}", 'error')

    safe_db_execute('redownload_element', 'records.subscription_rec', try_func=try_func, msg_func=msg_func, error_func=error_func)
