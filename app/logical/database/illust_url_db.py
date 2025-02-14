# APP/LOGICAL/DATABASE/ILLUST_URL_DB.PY

# ## LOCAL IMPORTS
from ...models import IllustUrl
from .base_db import set_column_attributes, save_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['site_name', 'url', 'sample_site_name', 'sample_url', 'width', 'height',
                        'order', 'active', 'post_id']
NULL_WRITABLE_ATTRIBUTES = ['illust_id']


# ## FUNCTIONS

# #### Create

def create_illust_url_from_parameters(createparams, commit=True):
    illust_url = IllustUrl()
    return set_illust_url_from_parameters(illust_url, createparams, 'created', commit)


# #### Update

def update_illust_url_from_parameters(illust_url, updateparams, commit=True):
    return set_illust_url_from_parameters(illust_url, updateparams, 'updated', commit)


# #### Set

def set_illust_url_from_parameters(illust_url, setparams, action, commit):
    if set_column_attributes(illust_url, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(illust_url, action, commit=commit)
    return illust_url


# #### Query

def get_illust_url_by_url(site, partial_url):
    q = IllustUrl.query
    if isinstance(site, int):
        q = q.filter(IllustUrl.site_id == site)
    elif isinstance(site, str):
        q = q.filter(IllustUrl.site_value == site)
    return q.filter(IllustUrl.url == partial_url).one_or_none()
