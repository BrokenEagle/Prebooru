# APP/LOGICAL/DATABASE/MEDIA_FILE_DB.PY

# ## PACKAGE IMPORTS
from utility.time import days_from_now, get_current_time

# ## LOCAL IMPORTS
from ...models import MediaFile
from .base_db import set_column_attributes, save_record, commit_session


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = []
NULL_WRITABLE_ATTRIBUTES = ['md5', 'file_ext', 'media_url']


# ## FUNCTIONS

# #### Create

def create_media_file_from_parameters(createparams):
    media_file = MediaFile(expires=days_from_now(1))
    return set_media_file_from_parameters(media_file, createparams, 'created')


# #### Update

def update_media_file_expires(media_file):
    media_file.expires = days_from_now(1)
    commit_session()


# #### Set

def set_media_file_from_parameters(media_file, setparams, action):
    if set_column_attributes(media_file, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(media_file, action)
    return media_file


# #### Delete

def batch_delete_media_files(media_files):
    id_list = [media.id for media in media_files]
    MediaFile.query.filter(MediaFile.id.in_(id_list)).delete()
    commit_session()


# #### Query functions

def get_media_file_by_id(id):
    return MediaFile.find(id)


def get_all_media_files():
    return MediaFile.query.all()


def get_expired_media_files():
    return MediaFile.query.filter(MediaFile.expires < get_current_time()).all()


def get_media_file_by_url(media_url):
    return MediaFile.query.filter_by(media_url=media_url).first()


def get_media_files_by_md5s(md5_list):
    return MediaFile.query.filter(MediaFile.md5.in_(md5_list)).all()


# ###### Test

def is_media_file(instance):
    return isinstance(instance, MediaFile)
