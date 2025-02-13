# APP/LOGICAL/DATABASE/ILLUST_URL_DB.PY

# ## LOCAL IMPORTS
from ...models import IllustUrl
from .base_db import set_column_attributes, save_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_ATTRIBUTES = ['site_name', 'url', 'sample_site_name', 'sample_url', 'width', 'height',
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
    if set_column_attributes(illust_url, ANY_WRITABLE_ATTRIBUTES, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(illust_url, action, commit=commit)
    return illust_url


# #### Query

def get_illust_url_by_full_url(full_url):
    from ..sites import site_name_by_url
    from ..sources import source_by_site_name
    site_name = site_name_by_url(full_url)
    source = source_by_site_name(site_name)
    partial = source.partial_media_url(full_url)
    return IllustUrl.query.filter(IllustUrl.site_value == site_name, IllustUrl.url == partial).one_or_none()
