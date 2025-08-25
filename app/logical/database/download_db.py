# APP/LOGICAL/DATABASE/DOWNLOAD_DB.PY

# ## LOCAL IMPORTS
from ...models import Download, DownloadUrl
from .base_db import set_column_attributes, add_record, save_record, commit_session, commit_or_flush


# ## GLOBAL VARIABLES

ANY_WRITABLE_ATTRIBUTES = ['status_name']
NULL_WRITABLE_ATTRIBUTES = ['request_url']


# ## FUNCTIONS

# #### Create

def create_download_from_parameters(createparams, commit=True):
    createparams.setdefault('status_name', 'pending')
    download = set_download_from_parameters(Download(), createparams, 'created', False)
    if 'image_urls' in createparams and len(createparams['image_urls']):
        _create_image_urls(download, createparams['image_urls'])
    commit_or_flush(commit)
    return download


# #### Update

def update_download_from_parameters(download, updateparams, commit=True):
    return set_download_from_parameters(download, updateparams, 'updated', commit)


# #### Set

def set_download_from_parameters(download, setparams, action, commit):
    if set_column_attributes(download, ANY_WRITABLE_ATTRIBUTES, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(download, action, commit=commit)
    return download


# #### Query

def get_pending_downloads():
    return Download.query.filter(Download.status_value == 'pending').all()


def get_processing_downloads():
    return Download.query.filter(Download.status_value == 'processing').all()


def get_pending_download_count():
    return Download.query.filter(Download.status_value == 'pending').get_count()


def get_processing_download_count():
    return Download.query.filter(Download.status_value == 'processing').get_count()


def get_download_by_request_url(request_url):
    return Download.query.filter(Download.request_url == request_url).one_or_none()


# #### Private

def _create_image_urls(download, urllist):
    for url in urllist:
        download_url = DownloadUrl(url=url, download_id=download.id)
        add_record(download_url)
    commit_session()
