# APP/DATABASE/ILLUST_URL_DB.PY

# ##LOCAL IMPORTS
from .. import models
from .base_db import UpdateColumnAttributes


# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['illust_id', 'site_id', 'url', 'width', 'height', 'order', 'active']

CREATE_ALLOWED_ATTRIBUTES = ['illust_id', 'site_id', 'url', 'width', 'height', 'order', 'active']
UPDATE_ALLOWED_ATTRIBUTES = ['site_id', 'url', 'width', 'height', 'order', 'active']


# ## FUNCTIONS

def CreateIllustUrlFromParameters(createparams):
    illust_url = models.IllustUrl()
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    UpdateColumnAttributes(illust_url, update_columns, createparams)
    return illust_url


def UpdateIllustUrlFromParameters(illust_url, updateparams):
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    UpdateColumnAttributes(illust_url, update_columns, updateparams)
