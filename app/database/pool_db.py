# APP/DATABASE/POOL_DB.PY

# ##LOCAL IMPORTS
from .. import models, SESSION
from ..logical.utility import GetCurrentTime
from .base_db import UpdateColumnAttributes


# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['name', 'series']

CREATE_ALLOWED_ATTRIBUTES = ['name', 'series']
UPDATE_ALLOWED_ATTRIBUTES = ['name', 'series']


# ## FUNCTIONS

# #### Route DB functions

# ###### Create

def CreatePoolFromParameters(createparams):
    current_time = GetCurrentTime()
    pool = models.Pool(created=current_time, updated=current_time, element_count=0)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    UpdateColumnAttributes(pool, update_columns, createparams)
    return pool


# ###### Update

def UpdatePoolFromParameters(pool, updateparams):
    update_results = []
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(UpdateColumnAttributes(pool, update_columns, updateparams))
    if any(update_results):
        print("Changes detected.")
        pool.updated = GetCurrentTime()
        SESSION.commit()
