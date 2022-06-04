# APP/LOGICAL/RECORDS/SUBSCRIPTION_REC.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import selectinload

# ## PACKAGE IMPORTS
from utility.time import days_from_now

# ## LOCAL IMPORTS
from ...models import Illust, IllustUrl
from ..searchable import search_attributes
from ..database.subscription_pool_element_db import create_subscription_pool_element_from_parameters
from ..database.jobs_db import get_job_status_data, update_job_status


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
    page = q.paginate(per_page=50)
    job_status['stage'] = 'elements'
    while True:
        print(f"update_subscription_elements: {page.first} - {page.last} / Total({page.total})")
        job_status['range'] = f"({page.first} - {page.last}) / {page.total}"
        update_job_status(job_id, job_status)
        for illust in page.items:
            if illust.type == 'image':
                illust_urls = illust.urls
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
