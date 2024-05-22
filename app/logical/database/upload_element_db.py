# APP/LOGICAL/DATABASE/UPLOAD_ELEMENT_DB.PY

# ## LOCAL IMPORTS
from ...enum_imports import upload_element_status
from ...models import UploadElement
from .base_db import set_column_attributes, save_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['status_id']
NULL_WRITABLE_ATTRIBUTES = ['upload_id', 'illust_url_id', 'media_asset_id']


# ## FUNCTIONS

# #### Route DB functions

# ###### CREATE

def create_upload_element_from_parameters(createparams, commit=True):
    createparams['status'] = 'pending'
    return set_upload_element_from_parameters(UploadElement(), createparams, commit, 'created')


# ###### UPDATE

# ###### Update

def update_upload_element_from_parameters(upload_element, updateparams, commit=True):
    return set_upload_element_from_parameters(upload_element, updateparams, commit, 'updated')


# #### Set

def set_upload_element_from_parameters(upload_element, setparams, commit, action):
    if 'status' in setparams:
        setparams['status_id'] = upload_element_status.by_name(setparams['status']).id
    if set_column_attributes(upload_element, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(upload_element, commit, action)
    return upload_element
