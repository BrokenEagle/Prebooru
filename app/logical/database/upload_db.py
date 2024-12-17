# APP/LOGICAL/DATABASE/UPLOAD_DB.PY

# ## PYTHON IMPORTS
import re

# ## LOCAL IMPORTS
from ...enum_imports import upload_status
from ...models import Upload, UploadUrl
from .base_db import set_column_attributes, add_record, save_record, commit_session, commit_or_flush


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['successes', 'failures', 'status_id']
NULL_WRITABLE_ATTRIBUTES = ['request_url', 'media_filepath', 'sample_filepath', 'illust_url_id']


# ## FUNCTIONS

# #### Create

def create_upload_from_parameters(createparams, commit=True):
    upload = Upload(successes=0, failures=0, status_id=upload_status.pending.id)
    set_upload_from_parameters(upload, createparams, 'created', False)
    if 'image_urls' in createparams and len(createparams['image_urls']):
        _create_image_urls(upload, createparams['image_urls'])
    commit_or_flush(commit)
    return upload


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


# #### Query

def get_pending_uploads():
    return Upload.query.enum_join(Upload.status_enum).filter(Upload.status_filter('name', '__eq__', 'pending')).all()


# #### Misc

def has_duplicate_posts(upload):
    return any(re.match(r'Image already uploaded on post #\d+', error.message) for error in upload.errors)


# #### Private

def _create_image_urls(upload, urllist):
    for url in urllist:
        upload_url = UploadUrl(url=url, upload_id=upload.id)
        add_record(upload_url)
    commit_session()
