# APP/LOGICAL/DATABASE/UPLOAD_DB.PY

# ## PYTHON IMPORTS
import re

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ... import SESSION
from ...enum_imports import upload_status
from ...models import Upload, UploadUrl
from .base_db import update_column_attributes, update_relationship_collections


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['illust_url_id', 'media_filepath', 'sample_filepath', 'request_url', 'active']

CREATE_ALLOWED_ATTRIBUTES = ['illust_url_id', 'media_filepath', 'sample_filepath', 'request_url', 'active',
                             'image_urls']


# ## FUNCTIONS

# #### DB Functions

# ###### CREATE

def create_upload_from_parameters(createparams):
    data = {
        'successes': 0,
        'failures': 0,
        'status_id': upload_status.pending.id,
        'created': get_current_time(),
    }
    upload = Upload(**data)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(upload, update_columns, createparams)
    if 'image_urls' in createparams and len(createparams['image_urls']):
        _update_illust_urls(upload, createparams['image_urls'])
    print("[%s]: created" % upload.shortlink)
    return upload


# #### Misc functions

def has_duplicate_posts(upload):
    return any(re.match(r'Image already uploaded on post #\d+', error.message) for error in upload.errors)


def set_upload_status(upload, value):
    upload.status_id = upload_status.by_name(value).id
    SESSION.commit()


def add_upload_success(upload):
    upload.successes += 1
    SESSION.commit()


def add_upload_failure(upload):
    upload.failures += 1
    SESSION.commit()


# #### Private

def _update_illust_urls(upload, urllist):
    for url in urllist:
        upload_url = UploadUrl(url=url, upload_id=upload.id)
        SESSION.add(upload_url)
