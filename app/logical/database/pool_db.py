# APP/LOGICAL/DATABASE/POOL_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import or_

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Pool
from .base_db import set_column_attributes, commit_or_flush


# ## GLOBAL VARIABLES

CREATE_ALLOWED_ATTRIBUTES = ['name', 'series']
UPDATE_ALLOWED_ATTRIBUTES = ['name', 'series']


# ## FUNCTIONS

# #### Route DB functions

# ###### Create

def create_pool_from_parameters(createparams, commit=True):
    current_time = get_current_time()
    pool = Pool(created=current_time, updated=current_time, element_count=0)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(Pool.all_columns)
    set_column_attributes(pool, update_columns, createparams)
    commit_or_flush(commit)
    print("[%s]: created" % pool.shortlink)
    return pool


# ###### Update

def update_pool_from_parameters(pool, updateparams, commit=True):
    update_results = []
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(set_column_attributes(pool, update_columns, updateparams))
    if any(update_results):
        pool.updated = get_current_time()
        commit_or_flush(commit)
        print("[%s]: updated" % pool.shortlink)


def update_pool_positions(pool):
    pool._elements.reorder()
    pool.element_count = pool._get_element_count()
    pool.checked = get_current_time()
    commit_or_flush(True)


# #### Query

def get_all_recheck_pools():
    return Pool.query.filter(or_(Pool.checked.is_(None), Pool.checked < Pool.updated)).all()
