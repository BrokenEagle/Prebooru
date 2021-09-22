# APP/DATABASE/POOL_DB.PY

# ##LOCAL IMPORTS
from .. import models, SESSION
from ..logical.utility import get_current_time
from .base_db import update_column_attributes


# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['name', 'series']

CREATE_ALLOWED_ATTRIBUTES = ['name', 'series']
UPDATE_ALLOWED_ATTRIBUTES = ['name', 'series']


# ## FUNCTIONS

# #### Route DB functions

# ###### Create

def create_pool_from_parameters(createparams):
    current_time = get_current_time()
    pool = models.Pool(created=current_time, updated=current_time, element_count=0)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(pool, update_columns, createparams)
    print("[%s]: created" % pool.shortlink)
    return pool


# ###### Update

def update_pool_from_parameters(pool, updateparams):
    update_results = []
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(update_column_attributes(pool, update_columns, updateparams))
    if any(update_results):
        print("[%s]: updated" % pool.shortlink)
        pool.updated = get_current_time()
        SESSION.commit()
