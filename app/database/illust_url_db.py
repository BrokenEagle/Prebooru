# APP/DATABASE/ILLUST_URL_DB.PY

# ##LOCAL IMPORTS
from .. import models
from .base_db import update_column_attributes


# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['illust_id', 'site_id', 'url', 'width', 'height', 'order', 'active']

CREATE_ALLOWED_ATTRIBUTES = ['illust_id', 'site_id', 'url', 'width', 'height', 'order', 'active']
UPDATE_ALLOWED_ATTRIBUTES = ['site_id', 'url', 'width', 'height', 'order', 'active']


# ## FUNCTIONS

def create_illust_url_from_parameters(createparams):
    illust_url = models.IllustUrl()
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(illust_url, update_columns, createparams)
    print("[%s]: created" % illust_url.shortlink)
    return illust_url


def update_illust_url_from_parameters(illust_url, updateparams):
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    if update_column_attributes(illust_url, update_columns, updateparams):
        print("[%s]: updated" % illust_url.shortlink)
