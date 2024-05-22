# APP/LOGICAL/DATABASE/POOL_ELEMENT_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import func

# ## LOCAL IMPORTS
from ...models import Illust, Post, Notation
from ...models.pool_element import PoolElement, PoolPost, PoolIllust, PoolNotation
from .base_db import set_column_attributes, commit_or_flush, save_record, delete_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['position']
NULL_WRITABLE_ATTRIBUTES = ['pool_id', 'post_id', 'illust_id', 'notation_id']

ID_MODEL_DICT = {
    'illust_id': Illust,
    'post_id': Post,
    'notation_id': Notation,
}

ELEMENT_DICT = {
    'post_id': PoolPost,
    'illust_id': PoolIllust,
    'notation_id': PoolNotation,
}


# ## FUNCTIONS

# #### Create

def create_pool_element_from_parameters(createparams, commit=True):
    item_key = next((key for key in createparams if key in ELEMENT_DICT))
    return set_pool_element_from_parameters(ELEMENT_DICT[item_key](), createparams, commit)


# #### Set

def set_pool_element_from_parameters(pool_element, setparams, commit):
    if set_column_attributes(pool_element, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(commit)
    return pool_element


# #### Delete

def delete_pool_element(pool_element):
    if pool_element.position >= (pool_element.pool.element_count - 1):
        # Only decrement the pool element count if the element is the last one. This will leave holes, which will be
        # fixed with a scheduled task, but will at least leave an elements position within range of the element count.
        pool_element.pool.element_count -= 1
    delete_record(pool_element)
    commit_or_flush(True)


# #### Query

def get_pool_max_position(pool_id):
    PoolElement.query.filter(PoolElement.pool_id == pool_id)\
                     .with_entities(func.max(PoolElement.position)).scalar()
