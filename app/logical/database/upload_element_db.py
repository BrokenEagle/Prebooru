# APP/LOGICAL/DATABASE/UPLOAD_ELEMENT_DB.PY

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Upload, UploadElement
from .base_db import update_column_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['upload_id', 'illust_url_id', 'md5', 'status']

CREATE_ALLOWED_ATTRIBUTES = ['upload_id', 'illust_url_id']
UPDATE_ALLOWED_ATTRIBUTES = ['md5', 'status']


# ## FUNCTIONS

# #### Route DB functions

# ###### CREATE

def create_upload_element_from_parameters(createparams, commit=True):
    upload_element = UploadElement(status='pending')
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(upload_element, update_columns, createparams, commit=commit)
    print("[%s]: created" % upload_element.shortlink)
    return upload_element


# ###### UPDATE

# ###### Update

def update_upload_element_from_parameters(upload_element, updateparams, commit=True):
    update_results = []
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(update_column_attributes(upload_element, update_columns, updateparams, commit=commit))
    if any(update_results):
        print("[%s]: updated" % upload_element.shortlink)
        if commit:
            SESSION.commit()
        else:
            SESSION.flush()
