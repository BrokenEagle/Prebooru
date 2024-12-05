# APP/LOGICAL/DATABASE/ILLUST_URL_DB.PY

# ## LOCAL IMPORTS
from ...models import IllustUrl
from ...enum_imports import site_descriptor
from .base_db import set_column_attributes, commit_or_flush, save_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['site_id', 'url', 'sample_site_id', 'sample_url', 'width', 'height',
                        'order', 'active', 'post_id']
NULL_WRITABLE_ATTRIBUTES = ['illust_id']


# ## FUNCTIONS

# #### Create

def create_illust_url_from_parameters(createparams, commit=True):
    return set_illust_url_from_parameters(IllustUrl(), createparams, commit, 'created')


# #### Update

def update_illust_url_from_parameters(illust_url, updateparams, commit=True):
    return set_illust_url_from_parameters(illust_url, updateparams, commit, 'updated')


# #### Set

def set_illust_url_from_parameters(illust_url, setparams, commit, action):
    if 'site' in setparams:
        setparams['site'] = IllustUrl.site_enum.by_name(setparams['site']).id
    if set_column_attributes(illust_url, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(illust_url, commit, action, safe=True)
    return illust_url


# #### Query

def get_illust_url_by_url(site, partial_url):
    if isinstance(site, int):
        enum_filter = IllustUrl.site_filter('id', '__eq__', site)
    elif isinstance(site, str):
        enum_filter = IllustUrl.site_filter('name', '__eq__', site)
    return IllustUrl.query.enum_join(IllustUrl.site_enum)\
                          .filter(enum_filter, IllustUrl.url == partial_url)\
                          .one_or_none()


# #### Misc

def set_url_site(dataparams, source):
    dataparams['site_id'] = site_descriptor.get_site_from_url(dataparams['url']).id
    dataparams['url'] = source.partial_media_url(dataparams['url'])
    dataparams['sample_site_id'] = site_descriptor.get_site_from_url(dataparams['sample']).id\
        if dataparams.get('sample') is not None else None
    dataparams['sample_url'] = source.partial_media_url(dataparams['sample'])\
        if dataparams.get('sample') is not None else None
