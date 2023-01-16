# APP/LOGICAL/DATABASE/NOTATION_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Notation, Pool, Booru, Artist, Illust, Post
from .pool_element_db import delete_pool_element
from .base_db import update_column_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['body']

CREATE_ALLOWED_ATTRIBUTES = ['body']
UPDATE_ALLOWED_ATTRIBUTES = ['body']

ID_MODEL_DICT = {
    'pool_id': Pool,
    'booru_id': Booru,
    'artist_id': Artist,
    'illust_id': Illust,
    'post_id': Post,
}


# ## FUNCTIONS

# #### Route DB functions

# ###### Create

def create_notation_from_parameters(createparams):
    current_time = get_current_time()
    notation = Notation(created=current_time, updated=current_time, no_pool=True)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(notation, update_columns, createparams)
    print("[%s]: created" % notation.shortlink)
    return notation


def create_notation_from_json(data):
    notation = Notation.loads(data)
    SESSION.add(notation)
    SESSION.commit()
    print("[%s]: created" % notation.shortlink)
    return notation


# ###### Update

def update_notation_from_parameters(notation, updateparams):
    update_results = []
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(update_column_attributes(notation, update_columns, updateparams))
    if any(update_results):
        print("[%s]: updated" % notation.shortlink)
        notation.updated = get_current_time()
        SESSION.commit()


# ###### Delete

def delete_notation(notation):
    if notation._pool is not None:
        delete_pool_element(notation._pool)
    SESSION.delete(notation)
    SESSION.commit()


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
    else:
        setattr(notation, table_name + '_id', item.id)
    SESSION.commit()
    return {'error': False}
