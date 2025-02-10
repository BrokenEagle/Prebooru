# APP/LOGICAL/DATABASE/NOTATION_DB.PY

# ## LOCAL IMPORTS
from ...models import Notation
from .base_db import set_column_attributes, save_record, set_timesvalue


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['body']
NULL_WRITABLE_ATTRIBUTES = ['no_pool', 'post_id', 'illust_id', 'artist_id', 'booru_id', 'created', 'updated']


# ## FUNCTIONS

# #### Create

def create_notation_from_parameters(createparams, commit=True):
    createparams.setdefault('no_pool', True)
    set_timesvalue(createparams, 'created')
    set_timesvalue(createparams, 'updated')
    return set_notation_from_parameters(Notation(), createparams, 'created', commit, True)


# #### Update

def update_notation_from_parameters(notation, updateparams, commit=True, update=True):
    return set_notation_from_parameters(notation, updateparams, 'updated', commit, update)


# #### Set

def set_notation_from_parameters(notation, setparams, action, commit, update):
    if set_column_attributes(notation, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams, update=update):
        save_record(notation, action, commit=commit)
    return notation
