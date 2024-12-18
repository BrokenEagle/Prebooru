# APP/LOGICAL/RECORDS/POOL_REC.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ...models import Pool, Illust, Post, Notation
from ..utility import set_error
from ..database.base_db import delete_record, commit_session
from ..database.pool_db import update_pool_from_parameters
from ..database.pool_element_db import create_pool_element_from_parameters


# ## GLOBAL VARIABLES

ID_MODEL_DICT = {
    'illust_id': Illust,
    'post_id': Post,
    'notation_id': Notation,
}


# ## FUNCTIONS

def add_to_pool(pool, dataparams):
    id_key = next((key for key in dataparams if key in ID_MODEL_DICT and dataparams[key] is not None))
    itemclass = ID_MODEL_DICT[id_key]
    itemtype = itemclass._model_name()
    id = dataparams[id_key]
    retdata = {'error': False, 'dataparams': dataparams}
    if isinstance(id, list):
        return add_items_to_pool(pool, id, id_key, itemclass, itemtype, retdata)
    else:
        return add_item_to_pool(pool, id, id_key, itemclass, itemtype, retdata)


def add_item_to_pool(pool, id, id_key, itemclass, itemtype, retdata):
    print('add_item_to_pool', pool, id, id_key, itemclass, itemtype, retdata)
    item = itemclass.find(id)
    if item is None:
        return set_error(retdata, "%s not found." % itemtype)
    pool_ids = list(set([pool_element.pool_id for pool_element in item._pools]))
    pool_element_ids = [pool_element.id for pool_element in item._pools]
    if pool.id in pool_ids:
        return set_error(retdata, "%s already added to %s." % (item.shortlink, pool.shortlink))
    next_position = pool.next_position
    params = {
        'pool_id': pool.id,
        id_key: id,
        'position': next_position,
    }
    element = create_pool_element_from_parameters(params, commit=False)
    update_pool_from_parameters(pool, {'element_count': next_position + 1}, commit=False)
    retdata.update({'pool': pool.basic_json(), 'type': itemtype, 'item': item.basic_json(),
                    'element_ids': pool_element_ids + [element.id], 'data': pool_ids + [pool.id]})
    commit_session()
    return retdata


def add_items_to_pool(pool, ids, id_key, itemclass, itemtype, retdata):
    items = itemclass.query.filter(itemclass.id.in_(ids)).all()
    if len(items) == 0:
        return set_error(retdata, "%ss not found." % itemtype)
    next_position = pool.next_position
    elements = []
    for i, item in enumerate(items):
        pool_ids = [pool_element.pool_id for pool_element in item._pools]
        if pool.id in pool_ids:
            continue
        params = {
            'pool_id': pool.id,
            id_key: item.id,
            'position': next_position + i,
        }
        element = create_pool_element_from_parameters(params, commit=False)
        elements.append(element)
    update_pool_from_parameters(pool, {'element_count': next_position + len(items)}, commit=False)
    pool_element_ids = [element.id for element in elements]
    retdata.update({'pool': pool.basic_json(), 'type': itemtype, 'element_ids': pool_element_ids})
    commit_session()
    return retdata


def update_pool_positions(pool):
    pool._elements.reorder()
    params = {'element_count': pool._get_element_count(), 'checked': get_current_time()}
    update_pool_from_parameters(pool, params, commit=True, update=False)


def delete_pool_element(pool_element):
    pool = pool_element.pool
    if pool_element.position >= (pool.element_count - 1):
        # Only decrement the pool element count if the element is the last one. This will leave holes, which will be
        # fixed with a scheduled task, but will at least leave an elements position within range of the element count.
        update_pool_from_parameters(pool, {'element_count': pool.element_count - 1}, commit=False)
    msg = "[%s]: deleted\n" % pool_element.shortlink
    delete_record(pool_element)
    commit_session()
    print(msg)


def batch_delete_pool_elements(pool_elements):
    pool_ids = set()
    element_ids = []
    for element in pool_elements:
        pool_ids.add(element.pool_id)
        element_ids.append(element.id)
        delete_record(element)
    commit_session()
    for pool_id in pool_ids:
        pool = Pool.find(pool_id)
        update_pool_positions(pool)
    print("Pool elements deleted:", element_ids, '\n')
