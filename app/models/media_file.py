# APP/MODELS/MEDIA_FILE.PY

# ## PYTHON IMPORTS
import os

# ## PACKAGE IMPORTS
from config import MEDIA_DIRECTORY
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel, BlobMD5, EpochTimestamp, image_server_url


# ## GLOBAL VARIABLES

CACHE_DATA_DIRECTORY = os.path.join(MEDIA_DIRECTORY, 'cache')


# ## CLASSES

class MediaFile(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    md5 = DB.Column(BlobMD5(nullable=False), nullable=False)
    file_ext = DB.Column(DB.String(255), nullable=False)
    media_url = DB.Column(DB.String(255), nullable=False)
    expires = DB.Column(EpochTimestamp(nullable=False), nullable=False)

    # ## Instance properties

    @property
    def file_url(self):
        return image_server_url(self._partial_network_path, 'main')

    @property
    def file_path(self):
        return os.path.join(CACHE_DATA_DIRECTORY, self._partial_file_path)

    @property
    def _partial_network_path(self):
        return 'cache/%s.%s' % (self.md5, self.file_ext)

    @property
    def _partial_file_path(self):
        return '%s.%s' % (self.md5, self.file_ext)

    # ## Class properties

    @classproperty(cached=True)
    def json_attributes(cls):
        return super().json_attributes + ['file_url']
