# APP/LOGICAL/DATABASE/POOL_ELEMENT_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import func

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Pool, Illust, Post, Notation
from ...models.pool_element import PoolElement, pool_element_create
from ..utility import set_error
from .pool_db import update_pool_positions


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


def batch_delete_pool_elements(pool_elements):
    pool_ids = set()
    for element in pool_elements:
        pool_ids.add(element.pool_id)
        SESSION.delete(element)
    SESSION.commit()
    for pool_id in pool_ids:
        pool = Pool.find(pool_id)
        update_pool_positions(pool)


# #### Query

def get_pool_elements_by_id(element_ids):
    return PoolElement.query.filter(PoolElement.id.in_(element_ids)).all()


# #### Misc

def create_pool_element_for_item(pool, id_key, dataparams):
    retdata = {'error': False, 'dataparams': dataparams}
    itemclass = ID_MODEL_DICT[id_key]
    itemtype = itemclass._model_name()
    id = dataparams[id_key]
    if isinstance(id, list):
        items = itemclass.query.filter(itemclass.id.in_(id)).all()
        if len(items) == 0:
            return set_error(retdata, "%ss not found." % itemtype)
        single = False
    else:
        item = itemclass.find(id)
        if item is None:
            return set_error(retdata, "%s not found." % itemtype)
        items = [item]
        single = True
    if pool.element_count > 0:
        max_position = PoolElement.query.filter(PoolElement.pool_id == pool.id)\
                                        .with_entities(func.max(PoolElement.position)).scalar()
    else:
        max_position = -1
    pool_ids = None
    for i, item in enumerate(items):
        pool_ids = [pool.id for pool in item.pools]
        if pool.id in pool_ids:
            if single:
                return set_error(retdata, "%s already added to %s." % (item.shortlink, pool.shortlink))
            else:
                continue
        new_element = pool_element_create(item)
        new_element.pool_id = pool.id
        new_element.position = max_position + i + 1
        SESSION.add(new_element)
        if single:
            pool_ids += [pool.id]
    pool.updated = get_current_time()
    pool.element_count = max_position + len(items) + 1
    SESSION.flush()
    if single:
        pool_element_ids = [pool_element.id for pool_element in item._pools]
        retdata.update({'pool': pool.basic_json(), 'type': itemtype, 'item': item.basic_json(),
                        'element_ids': pool_element_ids, 'data': pool_ids})
    SESSION.commit()
    return retdata
