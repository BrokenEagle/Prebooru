# APP/LOGICAL/DATABASE/POOL_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import or_

# ## LOCAL IMPORTS
from ...models import Pool
from .base_db import set_column_attributes, save_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['name', 'series', 'element_count']
NULL_WRITABLE_ATTRIBUTES = []


# ## FUNCTIONS

# #### Create

def create_pool_from_parameters(createparams, commit=True):
    pool = Pool(element_count=0)
    return set_pool_from_parameters(pool, createparams, 'created', commit, True)


# #### Update

def update_pool_from_parameters(pool, updateparams, commit=True, update=True):
    return set_pool_from_parameters(pool, updateparams, 'updated', commit, update)


# #### Set

def set_pool_from_parameters(pool, setparams, action, commit, update):
    if set_column_attributes(pool, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams, update=update):
        save_record(pool, action, commit=commit)
    return pool


# #### Query

def get_all_recheck_pools():
    return Pool.query.filter(or_(Pool.checked.is_(None), Pool.checked < Pool.updated)).all()
