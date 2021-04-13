# APP/DATABASE/UPLOAD_DB.PY

# ## PYTHON IMPORTS
import re

# ## LOCAL IMPORTS
from .. import models, SESSION
from ..logical.utility import GetCurrentTime
from .base_db import UpdateColumnAttributes, UpdateRelationshipCollections


# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['illust_url_id', 'media_filepath', 'sample_filepath', 'request_url', 'type', 'active']
UPDATE_SCALAR_RELATIONSHIPS = [('image_urls', 'url', models.UploadUrl)]

CREATE_ALLOWED_ATTRIBUTES = ['illust_url_id', 'media_filepath', 'sample_filepath', 'request_url', 'type', 'active', 'image_urls']


# ## FUNCTIONS

# #### DB Functions

# ###### CREATE

def CreateUploadFromParameters(createparams):
    data = {
        'successes': 0,
        'failures': 0,
        'status': 'pending',
        'subscription_id': None,
        'created': GetCurrentTime(),
    }
    upload = models.Upload(**data)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    UpdateColumnAttributes(upload, update_columns, createparams)
    create_relationships = [relationship for relationship in UPDATE_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    UpdateRelationshipCollections(upload, create_relationships, createparams)
    return upload


# #### Misc functions


def IsDuplicate(upload):
    return any(re.match(r'Image already uploaded on post #\d+', error.message) for error in upload.errors)


def SetUploadStatus(upload, status):
    upload.status = status
    SESSION.commit()


def AddUploadSuccess(upload):
    upload.successes += 1
    SESSION.commit()


def AddUploadFailure(upload):
    upload.failures += 1
    SESSION.commit()


def UploadAppendPost(upload, post):
    upload.posts.append(post)
    SESSION.commit()
