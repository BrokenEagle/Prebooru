# APP/LOGICAL/DATABASE/ILLUST_URL_DB.PY

# ## LOCAL IMPORTS
from ...models import IllustUrl
from ...enum_imports import site_descriptor
from .base_db import update_column_attributes, save_record


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['illust_id', 'site_id', 'url', 'sample_site_id', 'sample_url',
                     'width', 'height', 'order', 'active']

CREATE_ALLOWED_ATTRIBUTES = ['illust_id', 'site_id', 'url', 'sample_site_id', 'sample_url',
                             'width', 'height', 'order', 'active']
UPDATE_ALLOWED_ATTRIBUTES = ['site_id', 'url', 'sample_site_id', 'sample_url', 'width', 'height',
                             'order', 'active']


# ## FUNCTIONS

# #### Create

def create_illust_url_from_parameters(createparams):
    if 'site' in createparams:
        createparams['site_id'] = IllustUrl.site_enum.by_name(createparams['site']).id
    illust_url = IllustUrl()
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(illust_url, update_columns, createparams)
    save_record(illust_url, 'created')
    return illust_url


# #### Update

def update_illust_url_from_parameters(illust_url, updateparams):
    if 'site' in updateparams:
        updateparams['site'] = IllustUrl.site_enum.by_name(updateparams['site']).id
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    if update_column_attributes(illust_url, update_columns, updateparams):
        save_record(illust_url, 'updated')


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
