# APP/LOGICAL/DATABASE/DOWNLOAD_ELEMENT_DB.PY

# ## LOCAL IMPORTS
from ...enum_imports import download_element_status
from ...models import DownloadElement
from .base_db import set_column_attributes, save_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['status_id']
NULL_WRITABLE_ATTRIBUTES = ['download_id', 'illust_url_id', 'md5']


# ## FUNCTIONS

# #### Create

def create_download_element_from_parameters(createparams, commit=True):
    download_element = DownloadElement(status_id=download_element_status.pending.id)
    return set_download_element_from_parameters(download_element, createparams, 'created', commit)


# #### Update

def update_download_element_from_parameters(download_element, updateparams, commit=True):
    return set_download_element_from_parameters(download_element, updateparams, 'updated', commit)


# #### Set

def set_download_element_from_parameters(download_element, setparams, action, commit):
    if 'status' in setparams:
        setparams['status_id'] = DownloadElement.status_enum.by_name(setparams['status']).id
    if set_column_attributes(download_element, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(download_element, action, commit=commit)
    return download_element
