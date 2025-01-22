# APP/LOGICAL/DATABASE/UPLOAD_DB.PY

# ## LOCAL IMPORTS
from ...models import Upload
from .base_db import set_column_attributes, save_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['status_name']
NULL_WRITABLE_ATTRIBUTES = ['request_url', 'media_filepath', 'sample_filepath', 'illust_url_id']


# ## FUNCTIONS

# #### Create

def create_upload_from_parameters(createparams, commit=True):
    createparams.setdefault('status_name', 'pending')
    return set_upload_from_parameters(Upload(), createparams, 'created', commit)


# #### Update

def update_upload_from_parameters(upload, updateparams, commit=True):
    return set_upload_from_parameters(upload, updateparams, 'updated', commit)


# #### Set

def set_upload_from_parameters(upload, setparams, action, commit):
    if set_column_attributes(upload, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(upload, action, commit=commit)
    return upload
