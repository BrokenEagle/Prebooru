# APP/LOGICAL/DATABASE/POOL_ELEMENT_DB.PY

# ## LOCAL IMPORTS
from ...models import Pool, Illust, Post, Notation
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


# #### Query

def get_pool_elements_by_id(element_ids):
    return PoolElement.query.filter(PoolElement.id.in_(element_ids)).all()
