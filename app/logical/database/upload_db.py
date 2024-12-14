# APP/LOGICAL/DATABASE/UPLOAD_DB.PY

# ## PYTHON IMPORTS
import re

# ## LOCAL IMPORTS
from ...enum_imports import upload_status
from ...models import Upload, UploadUrl
from .base_db import set_column_attributes, add_record, save_record, commit_session, flush_session


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['successes', 'failures', 'status_id']
NULL_WRITABLE_ATTRIBUTES = ['request_url', 'media_filepath', 'sample_filepath', 'illust_url_id']


# ## FUNCTIONS

# #### DB Functions

# ###### CREATE

def create_upload_from_parameters(createparams):
    data = {
        'successes': 0,
        'failures': 0,
        'status_id': upload_status.pending.id,
    }
    upload = Upload(**data)
    set_column_attributes(upload, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, createparams)
    flush_session()
    if 'image_urls' in createparams and len(createparams['image_urls']):
        _update_illust_urls(upload, createparams['image_urls'])
    save_record(upload, 'created', commit=False)
    data = upload.to_json()
    commit_session()
    return data


# #### Query

def get_pending_uploads():
    return Upload.query.enum_join(Upload.status_enum).filter(Upload.status_filter('name', '__eq__', 'pending')).all()


# #### Misc functions

def has_duplicate_posts(upload):
    return any(re.match(r'Image already uploaded on post #\d+', error.message) for error in upload.errors)


def set_upload_status(upload, value):
    upload.status_id = upload_status.by_name(value).id
    commit_session()


def add_upload_success(upload):
    upload.successes += 1
    commit_session()


def add_upload_failure(upload):
    upload.failures += 1
    commit_session()


# #### Private

def _update_illust_urls(upload, urllist):
    for url in urllist:
        upload_url = UploadUrl(url=url, upload_id=upload.id)
        add_record(upload_url)
