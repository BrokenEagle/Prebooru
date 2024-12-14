# APP/LOGICAL/DATABASE/UPLOAD_ELEMENT_DB.PY

# ## LOCAL IMPORTS
from ...enum_imports import upload_element_status
from ...models import UploadElement
from .base_db import update_column_attributes, save_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['status_id']
NULL_WRITABLE_ATTRIBUTES = ['upload_id', 'illust_url_id', 'md5']


# ## FUNCTIONS

# #### Route DB functions

# ###### CREATE

def create_upload_element_from_parameters(createparams, commit=True):
    upload_element = UploadElement(status_id=upload_element_status.pending.id)
    update_column_attributes(upload_element, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, createparams)
    save_record(upload_element, 'created', commit=commit)
    return upload_element


# ###### UPDATE

# ###### Update

def update_upload_element_from_parameters(upload_element, updateparams, commit=True):
    if 'status' in updateparams:
        updateparams['status_id'] = UploadElement.status_enum.by_name(updateparams['status']).id
    if update_column_attributes(upload_element, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, updateparams):
        save_record(upload_element, 'updated', commit=commit)
