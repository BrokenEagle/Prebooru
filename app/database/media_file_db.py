from .. import SESSION
from ..models import MediaFile
from ..logical.utility import DaysFromNow
from ..logical.file import delete_file
from .base_db import UpdateColumnAttributes


# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['md5', 'file_ext', 'media_url']

CREATE_ALLOWED_ATTRIBUTES = ['md5', 'file_ext', 'media_url']


# ##FUNCTIONS

# #### DB functions

# ###### CREATE

def create_media_file_from_parameters(createparams):
    media_file = MediaFile(expires=DaysFromNow(1))
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    UpdateColumnAttributes(media_file, update_columns, createparams)
    print("[%s]: created" % media_file.shortlink)
    return media_file


# ###### DELETE

def delete_media_file(media_file):
    delete_file(media_file.file_path)
    SESSION.delete(media_file)
    SESSION.commit()


# #### Misc functions

def get_media_file_by_url(media_url):
    return MediaFile.query.filter_by(media_url=media_url).first()
