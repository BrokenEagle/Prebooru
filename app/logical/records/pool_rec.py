# APP/LOGICAL/RECORDS/POOL_REC.PY

# ## LOCAL IMPORTS
from ...models import Pool
from ..database.base_db import commit_or_flush
from ..database.pool_element_db import create_pool_element_from_parameters, get_pool_max_position


# ## GLOBAL VARIABLES

ID_MODEL_DICT = {
    'illust_id': Illust,
    'post_id': Post,
    'notation_id': Notation,
}


# ## FUNCTIONS

def add_element_to_pool(pool, params):
    id_key = next((key for key in params if key in ELEMENT_DICT))
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
        max_position = get_pool_max_position(pool.id)
    else:
        max_position = -1
    createparams['position'] = max_position + 1
    element = create_pool_element_from_parameters(createparams, commit=False)
    update_pool_from_parameters(pool, {'element_count': max_position + 2}, commit=False)
    pool_ids.append(pool.id)
    pool_element_ids = [pool_element.id for pool_element in item._pools]
    retdata.update({'pool': pool.basic_json(), 'type': itemtype, 'item': item.basic_json(),
                    'element_ids': pool_element_ids, 'data': pool_ids})
    commit_or_flush(True)
    return retdata


def update_pool_positions(pool):
    pool._elements.reorder()
    params = {'element_count', pool._get_element_count(), 'checked': get_current_time()}
    update_pool_from_parameters(pool, params, commit=True, update=False)
