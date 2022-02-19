# APP/LOGICAL/DATABASE/NOTATION_DB.PY

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Notation, Pool, Artist, Illust, Post
from ..utility import get_current_time
from .pool_element_db import delete_pool_element
from .base_db import update_column_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['body']

CREATE_ALLOWED_ATTRIBUTES = ['body']
UPDATE_ALLOWED_ATTRIBUTES = ['body']

ID_MODEL_DICT = {
    'pool_id': Pool,
    'artist_id': Artist,
    'illust_id': Illust,
    'post_id': Post,
}


# ## FUNCTIONS

# #### Route DB functions

# ###### Create

def create_notation_from_parameters(createparams):
    current_time = get_current_time()
    notation = Notation(created=current_time, updated=current_time)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(notation, update_columns, createparams)
    print("[%s]: created" % notation.shortlink)
    return notation


def create_notation_from_raw_parameters(createparams):
    notation = Notation()
    update_columns = set(createparams.keys()).intersection(Notation.archive_columns)
    update_column_attributes(notation, update_columns, createparams)
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
    table_name = model.__table__.name
    if item is None:
        msg = "Unable to add to %s; %s #%d does not exist." % (dataparams[append_key], table_name, table_name)
        return {'error': True, 'message': msg}
    if table_name == 'pool':
        item.elements.append(notation)
        item.updated = get_current_time()
        SESSION.commit()
        item.element_count = item._get_element_count()
        SESSION.commit()
    else:
        item.notations.append(notation)
    SESSION.commit()
    return {'error': False}
