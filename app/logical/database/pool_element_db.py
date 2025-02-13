# APP/LOGICAL/DATABASE/POOL_ELEMENT_DB.PY

# ## LOCAL IMPORTS
from ...models import PoolElement
from .base_db import set_column_attributes, save_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['position']
NULL_WRITABLE_ATTRIBUTES = ['pool_id', 'type_name', 'post_id', 'illust_id', 'notation_id']

ELEMENT_TYPE_DICT = {
    'post_id': 'pool_post',
    'illust_id': 'pool_illust',
    'notation_id': 'pool_notation',
}


# ## FUNCTIONS

# #### Create

def create_pool_element_from_parameters(createparams, commit=True):
    createparams['type_name'] = next((ELEMENT_TYPE_DICT[key] for key in createparams if key in ELEMENT_TYPE_DICT))
    return set_pool_element_from_parameters(PoolElement(), createparams, 'created', commit)


# #### Set

def set_pool_element_from_parameters(pool_element, setparams, action, commit):
    if set_column_attributes(pool_element, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(pool_element, action, commit=commit)
    return pool_element


# #### Query

def get_pool_elements_by_id(element_ids):
    return PoolElement.query.filter(PoolElement.id.in_(element_ids)).all()
