# APP/DATABASE/POOL_ELEMENT_DB.PY

# ##LOCAL IMPORTS
from .. import models, SESSION
from ..logical.utility import GetCurrentTime


# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['illust_id', 'site_id', 'url', 'width', 'height', 'order', 'active']

CREATE_ALLOWED_ATTRIBUTES = ['illust_id', 'site_id', 'url', 'width', 'height', 'order', 'active']
UPDATE_ALLOWED_ATTRIBUTES = ['site_id', 'url', 'width', 'height', 'order', 'active']

ID_MODEL_DICT = {
    'illust_id': models.Illust,
    'post_id': models.Post,
    'notation_id': models.Post,
}


# ## FUNCTIONS

# #### Route DB functions

# ###### CREATE

def CreatePoolElementFromParameters(pool, createparams):
    for key in ID_MODEL_DICT:
        if createparams[key] is not None:
            return AddTypeElement(pool, key, createparams)


# ###### DELETE

def DeletePoolElement(pool_element):
    pool = pool_element.pool
    SESSION.delete(pool_element)
    pool._elements.reorder()
    SESSION.commit()
    pool.element_count = pool._get_element_count()
    SESSION.commit()


# #### Misc

def AddTypeElement(pool, id_key, dataparams):
    itemclass = ID_MODEL_DICT[id_key]
    itemtype = itemclass.__table__.name
    id = dataparams[id_key]
    item = itemclass.find(id)
    if item is None:
        return {'error': True, 'message': "%s not found." % itemtype, 'dataparams': dataparams}
    pool_ids = [pool.id for pool in item.pools]
    if pool.id in pool_ids:
        return {'error': True, 'message': "%s #%d already added to pool #%d." % (itemtype, item.id, pool.id), 'dataparams': dataparams}
    pool.updated = GetCurrentTime()
    pool.elements.append(item)
    SESSION.commit()
    pool.element_count = pool._get_element_count()
    SESSION.commit()
    pool_ids += [pool.id]
    return {'error': False, 'pool': pool.to_json(), 'type': itemtype, 'item': item.to_json(), 'data': pool_ids, 'dataparams': dataparams}
