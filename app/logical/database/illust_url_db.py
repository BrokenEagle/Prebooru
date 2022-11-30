# APP/LOGICAL/DATABASE/ILLUST_URL_DB.PY

# ## LOCAL IMPORTS
from ...models import IllustUrl
from .base_db import update_column_attributes


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
    print("[%s]: created" % illust_url.shortlink)
    return illust_url


# #### Update

def update_illust_url_from_parameters(illust_url, updateparams):
    if 'site' in updateparams:
        updateparams['site'] = IllustUrl.site_enum.by_name(updateparams['site']).id
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    if update_column_attributes(illust_url, update_columns, updateparams):
        print("[%s]: updated" % illust_url.shortlink)


# #### Query

def get_illust_url_by_url(site_id, partial_url):
    return IllustUrl.query.enum_join(IllustUrl.site_enum)\
                          .filter(IllustUrl.site_filter('id', '__eq__', site_id),
                                  IllustUrl.url == partial_url)\
                          .one_or_none()
