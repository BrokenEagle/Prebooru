# APP/LOGICAL/DATABASE/UPLOAD_ELEMENT_DB.PY

# ## LOCAL IMPORTS
from ... import SESSION
from ...enum_imports import upload_element_status
from ...models import UploadElement
from .media_asset_db import get_media_asset_by_md5
from .base_db import set_column_attributes, commit_or_flush


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['upload_id', 'illust_url_id', 'status_id']

CREATE_ALLOWED_ATTRIBUTES = ['upload_id', 'illust_url_id']
UPDATE_ALLOWED_ATTRIBUTES = ['status_id']


# ## FUNCTIONS

# #### Route DB functions

# ###### CREATE

def create_upload_element_from_parameters(createparams, commit=True):
    upload_element = UploadElement(status_id=upload_element_status.pending.id)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    set_column_attributes(upload_element, update_columns, createparams)
    commit_or_flush(commit)
    print("[%s]: created" % upload_element.shortlink)
    return upload_element


# ###### UPDATE

# ###### Update

def update_upload_element_from_parameters(upload_element, updateparams, commit=True):
    update_results = []
    if 'md5' in updateparams:
        upload_element.media = get_media_asset_by_md5(updateparams['md5'])
        update_results.append(True)
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(set_column_attributes(upload_element, update_columns, updateparams))
    if any(update_results):
        commit_or_flush(commit)
        print("[%s]: updated" % upload_element.shortlink)


# #### Misc

def link_upload_media(element, post):
    element.media_asset_id = post.media_asset_id
    element.status_id = upload_element_status.complete.id
    SESSION.commit()
