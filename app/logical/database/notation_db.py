# APP/LOGICAL/DATABASE/NOTATION_DB.PY

# ## LOCAL IMPORTS
from ...models import Notation
from .base_db import set_column_attributes, add_record, save_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['body']
NULL_WRITABLE_ATTRIBUTES = []


# ## FUNCTIONS

# #### Create

def create_notation_from_parameters(createparams, commit=True):
    notation = Notation(no_pool=True)
    return set_notation_from_parameters(notation, createparams, 'created', commit, True)


def create_notation_from_json(data):
    notation = Notation.loads(data)
    add_record(notation)
    save_record(notation, 'created')
    return notation


# #### Update

def update_notation_from_parameters(notation, updateparams, commit=True, update=True):
    return set_notation_from_parameters(notation, updateparams, 'updated', commit, update)


# #### Set

def set_notation_from_parameters(notation, setparams, action, commit, update):
    if set_column_attributes(notation, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams, update=update):
        save_record(notation, action, commit=commit)
    return notation
