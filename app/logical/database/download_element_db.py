# APP/LOGICAL/DATABASE/DOWNLOAD_ELEMENT_DB.PY

# ## LOCAL IMPORTS
from ...models import DownloadElement
from .base_db import set_column_attributes, save_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['status_name']
NULL_WRITABLE_ATTRIBUTES = ['download_id', 'illust_url_id', 'md5']


# ## FUNCTIONS

# #### Create

def create_download_element_from_parameters(createparams, commit=True):
    createparams.setdefault('status_name', 'pending')
    return set_download_element_from_parameters(DownloadElement(), createparams, 'created', commit)


# #### Update

def update_download_element_from_parameters(download_element, updateparams, commit=True):
    return set_download_element_from_parameters(download_element, updateparams, 'updated', commit)


# #### Set

def set_download_element_from_parameters(download_element, setparams, action, commit):
    if set_column_attributes(download_element, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(download_element, action, commit=commit)
    return download_element
