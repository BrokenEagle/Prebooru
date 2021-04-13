# APP/DATABASE/ARTIST_DB.PY

# ##LOCAL IMPORTS
from .. import models, SESSION
from ..logical.utility import GetCurrentTime
from .base_db import UpdateColumnAttributes


# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['body']

CREATE_ALLOWED_ATTRIBUTES = ['body']
UPDATE_ALLOWED_ATTRIBUTES = ['body']

ID_MODEL_DICT = {
    'pool_id': models.Pool,
    'artist_id': models.Artist,
    'illust_id': models.Illust,
    'post_id': models.Post,
}


# ## FUNCTIONS

# #### Route DB functions

# ###### Create

def CreateNotationFromParameters(createparams):
    current_time = GetCurrentTime()
    notation = models.Notation(created=current_time, updated=current_time)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    UpdateColumnAttributes(notation, update_columns, createparams)
    return notation


# ###### Update

def UpdateNotationFromParameters(notation, updateparams):
    update_results = []
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(UpdateColumnAttributes(notation, update_columns, updateparams))
    if any(update_results):
        print("Changes detected.")
        notation.updated = GetCurrentTime()
        SESSION.commit()


# ###### Delete

def DeleteNotation(notation):
    pool = notation.pool
    SESSION.delete(notation)
    SESSION.commit()
    if pool is not None:
        pool._elements.reorder()
        SESSION.commit()


# #### Misc functions

def AppendToItem(notation, append_key, dataparams):
    model = ID_MODEL_DICT[append_key]
    item = model.find(dataparams[append_key])
    table_name = model.__table__.name
    if item is None:
        return {'error': True, 'message': 'Unable to add to %s; %s #%d does not exist.' % (dataparams[append_key], table_name, table_name)}
    if table_name == 'pool':
        item.elements.append(notation)
    else:
        item.notations.append(notation)
    SESSION.commit()
    return {'error': False}
