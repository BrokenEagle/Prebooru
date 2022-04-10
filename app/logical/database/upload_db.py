# APP/LOGICAL/DATABASE/UPLOAD_DB.PY

# ## PYTHON IMPORTS
import re

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Upload, UploadUrl
from .base_db import update_column_attributes, update_relationship_collections


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['illust_url_id', 'media_filepath', 'sample_filepath', 'request_url', 'type', 'active']
UPDATE_SCALAR_RELATIONSHIPS = [('image_urls', 'url', UploadUrl)]

CREATE_ALLOWED_ATTRIBUTES = ['illust_url_id', 'media_filepath', 'sample_filepath', 'request_url', 'type', 'active',
                             'image_urls']


# ## FUNCTIONS

# #### DB Functions

# ###### CREATE

def create_upload_from_parameters(createparams):
    data = {
        'successes': 0,
        'failures': 0,
        'status': 'pending',
        'created': get_current_time(),
    }
    upload = Upload(**data)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(upload, update_columns, createparams)
    create_relationships = [rel for rel in UPDATE_SCALAR_RELATIONSHIPS if rel[0] in settable_keylist]
    update_relationship_collections(upload, create_relationships, createparams)
    print("[%s]: created" % upload.shortlink)
    return upload


# #### Misc functions

def has_duplicate_posts(upload):
    return any(re.match(r'Image already uploaded on post #\d+', error.message) for error in upload.errors)


def set_upload_status(upload, status):
    upload.status = status
    SESSION.commit()


def add_upload_success(upload):
    upload.successes += 1
    SESSION.commit()


def add_upload_failure(upload):
    upload.failures += 1
    SESSION.commit()


def upload_append_post(upload, post):
    upload.posts.append(post)
    SESSION.commit()
