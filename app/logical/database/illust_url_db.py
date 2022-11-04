# APP/LOGICAL/DATABASE/ILLUST_URL_DB.PY

# ## LOCAL IMPORTS
from ...models import IllustUrl
from .base_db import update_column_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['illust_id', 'site', 'url', 'sample_site', 'sample_url', 'width', 'height', 'order', 'active']

CREATE_ALLOWED_ATTRIBUTES = ['illust_id', 'site', 'url', 'sample_site', 'sample_url', 'width', 'height', 'order',
                             'active']
UPDATE_ALLOWED_ATTRIBUTES = ['site', 'url', 'sample_site', 'sample_url', 'width', 'height', 'order', 'active']


# ## FUNCTIONS

# #### Create

def create_illust_url_from_parameters(createparams):
    illust_url = IllustUrl()
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(illust_url, update_columns, createparams)
    print("[%s]: created" % illust_url.shortlink)
    return illust_url


# #### Update

def update_illust_url_from_parameters(illust_url, updateparams):
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    if update_column_attributes(illust_url, update_columns, updateparams):
        print("[%s]: updated" % illust_url.shortlink)


# #### Query

def get_illust_url_by_url(site=None, partial_url=None, full_url=None):
    from ..sources.base import get_illust_url_params
    if (site is None or partial_url is None):
        if full_url is None:
            return
        site, partial_url = get_illust_url_params(full_url)
    return IllustUrl.query.filter_by(site=site, url=partial_url).first()
