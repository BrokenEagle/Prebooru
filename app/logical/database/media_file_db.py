# APP/LOGICAL/DATABASE/MEDIA_FILE_DB.PY

# ## PACKAGE IMPORTS
from utility.time import days_from_now, get_current_time

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import MediaFile
from .base_db import set_column_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['md5', 'file_ext', 'media_url']

CREATE_ALLOWED_ATTRIBUTES = ['md5', 'file_ext', 'media_url']


# ## FUNCTIONS

# #### DB functions

# ###### CREATE

def create_media_file_from_parameters(createparams):
    media_file = MediaFile(expires=days_from_now(1))
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    set_column_attributes(media_file, update_columns, createparams)
    print("[%s]: created" % media_file.shortlink)
    return media_file


# ###### UPDATE

def update_media_file_expires(media_file):
    media_file.expires = days_from_now(1)
    SESSION.commit()


# ###### DELETE

def batch_delete_media_files(media_files):
    id_list = [media.id for media in media_files]
    MediaFile.query.filter(MediaFile.id.in_(id_list)).delete()
    SESSION.commit()


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
