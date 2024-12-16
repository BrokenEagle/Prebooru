# APP/LOGICAL/DATABASE/POOL_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import or_

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ...models import Pool
from .base_db import set_column_attributes, save_record, commit_session


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['name', 'series', 'element_count']
NULL_WRITABLE_ATTRIBUTES = []


# ## FUNCTIONS

# #### Create

def create_pool_from_parameters(createparams):
    pool = Pool(element_count=0)
    return set_pool_from_parameters(pool, createparams, 'created')


# #### Update

def update_pool_from_parameters(pool, updateparams):
    return set_pool_from_parameters(pool, updateparams, 'updated')


def update_pool_positions(pool):
    pool._elements.reorder()
    pool.element_count = pool._get_element_count()
    pool.checked = get_current_time()
    commit_session()


# #### Set

def set_pool_from_parameters(pool, setparams, action):
    if set_column_attributes(pool, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(pool, action)
    return pool


# #### Query

def get_all_recheck_pools():
    return Pool.query.filter(or_(Pool.checked.is_(None), Pool.checked < Pool.updated)).all()
