# APP/LOGICAL/DATABASE/POOL_ELEMENT_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import func

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Illust, Post, Notation
from ...models.pool_element import PoolElement, pool_element_create
from ..utility import set_error


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['illust_id', 'site', 'url', 'width', 'height', 'order', 'active']

CREATE_ALLOWED_ATTRIBUTES = ['illust_id', 'site', 'url', 'width', 'height', 'order', 'active']
UPDATE_ALLOWED_ATTRIBUTES = ['site', 'url', 'width', 'height', 'order', 'active']

ID_MODEL_DICT = {
    'illust_id': Illust,
    'post_id': Post,
    'notation_id': Notation,
}


# ## FUNCTIONS

# #### Route DB functions

# ###### CREATE

def create_pool_element_from_parameters(pool, createparams):
    for key in ID_MODEL_DICT:
        if createparams[key] is not None:
            return create_pool_element_for_item(pool, key, createparams)


# ###### DELETE

def delete_pool_element(pool_element):
    if pool_element.position >= (pool_element.pool.element_count - 1):
        # Only decrement the pool element count if the element is the last one. This will leave holes, which will be
        # fixed with a scheduled task, but will at least leave an elements position within range of the element count.
        pool_element.pool.element_count -= 1
    SESSION.delete(pool_element)
    SESSION.commit()


# #### Misc

def create_pool_element_for_item(pool, id_key, dataparams):
    itemclass = ID_MODEL_DICT[id_key]
    itemtype = itemclass._model_name()
    id = dataparams[id_key]
    item = itemclass.find(id)
    retdata = {'error': False, 'dataparams': dataparams}
    if item is None:
        return set_error(retdata, "%s not found." % itemtype)
    pool_ids = [pool.id for pool in item.pools]
    if pool.id in pool_ids:
        return set_error(retdata, "%s already added to %s." % (item.shortlink, pool.shortlink))
    if pool.element_count > 0:
        max_position = PoolElement.query.filter(PoolElement.pool_id == pool.id)\
                                        .with_entities(func.max(PoolElement.position)).scalar()
    else:
        max_position = -1
    pool.updated = get_current_time()
    new_element = pool_element_create(item)
    new_element.pool_id = pool.id
    new_element.position = max_position + 1
    SESSION.add(new_element)
    pool.element_count = max_position + 2
    SESSION.flush()
    pool_ids += [pool.id]
    pool_element_ids = [pool_element.id for pool_element in item._pools]
    retdata.update({'pool': pool.basic_json(), 'type': itemtype, 'item': item.basic_json(),
                    'element_ids': pool_element_ids, 'data': pool_ids})
    SESSION.commit()
    return retdata
