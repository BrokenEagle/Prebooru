# APP/LOGICAL/DATABASE/NOTATION_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ...models import Notation, Pool, Subscription, Booru, Artist, Illust, Post
from .base_db import set_column_attributes, commit_or_flush, save_record, add_record, delete_record


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
    return set_notation_from_parameters(Notation(no_pool=True), createparams, commit, 'created', False)


def create_notation_from_json(data):
    notation = Notation.loads(data)
    add_record(notation)
    save_record(notation, True, 'created')
    print("[%s]: created" % notation.shortlink)
    return notation


# #### Update

def update_notation_from_parameters(notation, updateparams, commit=True, update=False):
    return set_notation_from_parameters(notation, updateparams, commit, 'updated', update)


# #### Set

def set_notation_from_parameters(notation, setparams, commit, action, update):
    if set_column_attributes(notation, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams, update):
        save_record(notation, commit, action)
    return notation


# #### Misc functions

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
        commit_or_flush(False)
        item = notation._pool
    else:
        setattr(notation, table_name + '_id', item.id)
    commit_or_flush(True)
    return {'error': False, 'append_item': item.to_json(), 'append_type': item.model_name}
