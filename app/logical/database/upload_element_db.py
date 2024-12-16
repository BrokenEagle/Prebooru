# APP/LOGICAL/DATABASE/UPLOAD_ELEMENT_DB.PY

# ## LOCAL IMPORTS
from ...enum_imports import upload_element_status
from ...models import UploadElement
from .base_db import set_column_attributes, save_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['status_id']
NULL_WRITABLE_ATTRIBUTES = ['upload_id', 'illust_url_id', 'md5']


# ## FUNCTIONS

# #### Create

def create_upload_element_from_parameters(createparams, commit=True):
    upload_element = UploadElement(status_id=upload_element_status.pending.id)
    return set_upload_element_from_parameters(upload_element, createparams, 'created', commit)


# #### Update

def update_upload_element_from_parameters(upload_element, updateparams, commit=True):
    return set_upload_element_from_parameters(upload_element, updateparams, 'updated', commit)


# #### Set

def set_upload_element_from_parameters(upload_element, setparams, action, commit):
    if 'status' in setparams:
        setparams['status_id'] = UploadElement.status_enum.by_name(setparams['status']).id
    if set_column_attributes(upload_element, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(upload_element, action, commit=commit)
    return upload_element
