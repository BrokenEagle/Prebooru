# APP/LOGICAL/DATABASE/UPLOAD_ELEMENT_DB.PY

# ## LOCAL IMPORTS
from ...enum_imports import upload_element_status
from ...models import UploadElement
from .base_db import update_column_attributes, save_record


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['upload_id', 'illust_url_id', 'md5', 'status_id']

CREATE_ALLOWED_ATTRIBUTES = ['upload_id', 'illust_url_id']
UPDATE_ALLOWED_ATTRIBUTES = ['md5', 'status_id']


# ## FUNCTIONS

# #### Route DB functions

# ###### CREATE

def create_upload_element_from_parameters(createparams, commit=True):
    upload_element = UploadElement(status_id=upload_element_status.pending.id)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(upload_element, update_columns, createparams)
    save_record(upload_element, 'created', commit=commit)
    return upload_element


# ###### UPDATE

# ###### Update

def update_upload_element_from_parameters(upload_element, updateparams, commit=True):
    update_results = []
    if 'status' in updateparams:
        updateparams['status_id'] = UploadElement.status_enum.by_name(updateparams['status']).id
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(update_column_attributes(upload_element, update_columns, updateparams))
    if any(update_results):
        save_record(upload_element, 'updated', commit=commit)
