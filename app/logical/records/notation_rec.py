# APP/LOGICAL/RECORDS/NOTATION_REC.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ...models import Pool, Subscription, Booru, Artist, Illust, Post
from ..database.pool_element_db import create_pool_element_from_parameters
from ..database.base_db import delete_record, commit_session, flush_session
from .pool_rec import delete_pool_element

# ## GLOBAL VARIABLES

ID_MODEL_DICT = {
    'pool_id': Pool,
    'subscription_id': Subscription,
    'booru_id': Booru,
    'artist_id': Artist,
    'illust_id': Illust,
    'post_id': Post,
}


# ## FUNCTIONS

def append_notation_to_item(notation, append_key, dataparams):
    model = ID_MODEL_DICT[append_key]
    item = model.find(dataparams[append_key])
    table_name = item.table_name
    if item is None:
        msg = "Unable to add to %s; %s #%d does not exist." % (dataparams[append_key], table_name, table_name)
        return {'error': True, 'message': msg}
    if table_name == 'pool':
        params = {
            'pool_id': item.id,
            'notation_id': notation.id,
            'position': item.next_position,
        }
        create_pool_element_from_parameters(params, commit=False)
        item.updated = get_current_time()
        item.element_count += 1
        notation.no_pool = False
        flush_session()
        item = notation.pool_element
    else:
        setattr(notation, table_name + '_id', item.id)
    commit_session()
    return {'error': False, 'append_item': item.to_json(), 'append_type': item.model_name}


def delete_notation(notation):
    msg = "[%s]: deleted\n" % notation.shortlink
    if notation.pool_element is not None:
        delete_pool_element(notation.pool_element)
    delete_record(notation)
    commit_session()
    print(msg)
