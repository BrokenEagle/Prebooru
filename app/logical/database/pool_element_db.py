# APP/LOGICAL/DATABASE/POOL_ELEMENT_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Illust, Post, Notation
from ..utility import set_error


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['illust_id', 'site_id', 'url', 'width', 'height', 'order', 'active']

CREATE_ALLOWED_ATTRIBUTES = ['illust_id', 'site_id', 'url', 'width', 'height', 'order', 'active']
UPDATE_ALLOWED_ATTRIBUTES = ['site_id', 'url', 'width', 'height', 'order', 'active']

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
    pool = pool_element.pool
    SESSION.delete(pool_element)
    pool._elements.reorder()
    SESSION.commit()
    pool.element_count = pool._get_element_count()
    SESSION.commit()


# #### Misc

def create_pool_element_for_item(pool, id_key, dataparams):
    itemclass = ID_MODEL_DICT[id_key]
    itemtype = itemclass.__table__.name
    id = dataparams[id_key]
    item = itemclass.find(id)
    retdata = {'error': False, 'dataparams': dataparams}
    if item is None:
        return set_error(retdata, "%s not found." % itemtype)
    pool_ids = [pool.id for pool in item.pools]
    if pool.id in pool_ids:
        return set_error(retdata, "%s #%d already added to pool #%d." % (itemtype, item.id, pool.id))
    pool.updated = get_current_time()
    pool.elements.append(item)
    SESSION.commit()
    pool.element_count = pool._get_element_count()
    SESSION.commit()
    pool_ids += [pool.id]
    retdata.update({'pool': pool.to_json(), 'type': itemtype, 'item': item.to_json(), 'data': pool_ids})
    return retdata
