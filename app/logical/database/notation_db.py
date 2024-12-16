# APP/LOGICAL/DATABASE/NOTATION_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ...models import Notation, Pool, Subscription, Booru, Artist, Illust, Post
from .pool_element_db import delete_pool_element
from .base_db import set_column_attributes, add_record, delete_record, save_record, commit_session, flush_session


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['body']
NULL_WRITABLE_ATTRIBUTES = []

ID_MODEL_DICT = {
    'pool_id': Pool,
    'subscription_id': Subscription,
    'booru_id': Booru,
    'artist_id': Artist,
    'illust_id': Illust,
    'post_id': Post,
}


# ## FUNCTIONS

# #### Create

def create_notation_from_parameters(createparams, commit=True):
    notation = Notation(no_pool=True)
    return set_notation_from_parameters(notation, createparams, 'created', commit)


def create_notation_from_json(data):
    notation = Notation.loads(data)
    add_record(notation)
    save_record(notation, 'created')
    return notation


# #### Update

def update_notation_from_parameters(notation, updateparams, commit=True):
    return set_notation_from_parameters(notation, updateparams, 'updated', commit)


# #### Set

def set_notation_from_parameters(notation, setparams, action, commit):
    if set_column_attributes(notation, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(notation, action, commit=commit)
    return notation


# #### Delete

def delete_notation(notation):
    if notation._pool is not None:
        delete_pool_element(notation._pool)
    delete_record(notation)
    commit_session()


# #### Misc

def append_notation_to_item(notation, append_key, dataparams):
    model = ID_MODEL_DICT[append_key]
    item = model.find(dataparams[append_key])
    table_name = item.table_name
    if item is None:
        msg = "Unable to add to %s; %s #%d does not exist." % (dataparams[append_key], table_name, table_name)
        return {'error': True, 'message': msg}
    if table_name == 'pool':
        item.elements.append(notation)
        item.updated = get_current_time()
        item.element_count += 1
        notation.no_pool = False
        flush_session()
        item = notation._pool
    else:
        setattr(notation, table_name + '_id', item.id)
    commit_session()
    return {'error': False, 'append_item': item.to_json(), 'append_type': item.model_name}
