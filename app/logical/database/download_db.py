# APP/LOGICAL/DATABASE/DOWNLOAD_DB.PY

# ## LOCAL IMPORTS
from ...enum_imports import download_status
from ...models import Download, DownloadUrl
from .base_db import set_column_attributes, add_record, save_record, commit_session, commit_or_flush


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['status_id']
NULL_WRITABLE_ATTRIBUTES = ['request_url']


# ## FUNCTIONS

# #### Create

def create_download_from_parameters(createparams, commit=True):
    download = Download(status_id=download_status.pending.id)
    set_download_from_parameters(download, createparams, 'created', False)
    if 'image_urls' in createparams and len(createparams['image_urls']):
        _create_image_urls(download, createparams['image_urls'])
    commit_or_flush(commit)
    return download


# #### Update

def update_download_from_parameters(download, updateparams, commit=True):
    return set_download_from_parameters(download, updateparams, 'updated', commit)


# #### Set

def set_download_from_parameters(download, setparams, action, commit):
    if 'status' in setparams:
        setparams['status_id'] = Download.status_enum.by_name(setparams['status']).id
    if set_column_attributes(download, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(download, action, commit=commit)
    return download


# #### Query

def get_pending_downloads():
    return Download.query.enum_join(Download.status_enum)\
                         .filter(Download.status_filter('name', '__eq__', 'pending'))\
                         .all()


# #### Private

def _create_image_urls(download, urllist):
    for url in urllist:
        download_url = DownloadUrl(url=url, download_id=download.id)
        add_record(download_url)
    commit_session()
