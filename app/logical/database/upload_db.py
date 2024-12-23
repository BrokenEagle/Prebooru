# APP/LOGICAL/DATABASE/UPLOAD_DB.PY

# ## LOCAL IMPORTS
from ...enum_imports import upload_status
from ...models import Upload
from .base_db import set_column_attributes, save_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['status_id']
NULL_WRITABLE_ATTRIBUTES = ['request_url', 'media_filepath', 'sample_filepath', 'illust_url_id']


# ## FUNCTIONS

# #### Create

def create_upload_from_parameters(createparams, commit=True):
    upload = Upload(status_id=upload_status.pending.id)
    return set_upload_from_parameters(upload, createparams, 'created', commit)


# #### Update

def update_upload_from_parameters(upload, updateparams, commit=True):
    return set_upload_from_parameters(upload, updateparams, 'updated', commit)


# #### Set

def set_upload_from_parameters(upload, setparams, action, commit):
    if 'status' in setparams:
        setparams['status_id'] = Upload.status_enum.by_name(setparams['status']).id
    if set_column_attributes(upload, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(upload, action, commit=commit)
    return upload
