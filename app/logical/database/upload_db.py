# APP/LOGICAL/DATABASE/UPLOAD_DB.PY

# ## PACKAGE IMPORTS
from utility.data import merge_dicts

# ## LOCAL IMPORTS
from ...enum_imports import upload_status
from ...models import Upload, UploadUrl
from .error_db import append_error
from .base_db import set_column_attributes, set_relationship_collections, commit_or_flush, save_record


# ## GLOBAL VARIABLES

ALL_SCALAR_RELATIONSHIPS = [('image_urls', 'url', UploadUrl)]

ANY_WRITABLE_COLUMNS = ['successes', 'failures', 'status_id']
NULL_WRITABLE_ATTRIBUTES = ['request_url', 'media_filepath', 'sample_filepath', 'illust_url_id']


# ## FUNCTIONS

# #### DB Functions

# ###### CREATE

def create_upload_from_parameters(createparams, commit=True):
    defaultparams = {
        'successes': 0,
        'failures': 0,
        'status': 'pending',
    }
    mergedparams = merge_dicts(defaultparams, createparams)
    return set_upload_from_parameters(Upload(), mergedparams, commit, 'created')


# #### Update

def update_upload_from_parameters(upload, updateparams, commit=True):
    return set_upload_from_parameters(upload, updateparams, commit, 'updated')


# #### Set

def set_upload_from_parameters(upload, setparams, commit, action):
    if 'status' in setparams:
        setparams['status_id'] = upload_status.by_name(setparams['status']).id
    col_result = set_column_attributes(upload, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams)
    if col_result:
        commit_or_flush(False, safe=True)
    rel_result = set_relationship_collections(upload, ALL_SCALAR_RELATIONSHIPS, setparams)
    if any([col_result, rel_result]):
        save_record(upload, commit, action)
    return upload


# #### Query

def get_pending_uploads():
    return Upload.query.enum_join(Upload.status_enum).filter(Upload.status_filter('name', '__eq__', 'pending')).all()


# #### Misc

def add_upload_error(upload, error):
    append_error(upload, error, commit=False)
    update_upload_from_parameters(upload, {'status': 'error'}, commit=True)
