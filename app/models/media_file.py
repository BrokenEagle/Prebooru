# APP/MODELS/MEDIA_FILE.PY

# ## PYTHON IMPORTS
import os

# ## PACKAGE IMPORTS
from config import MEDIA_DIRECTORY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel, image_server_url, classproperty


# ## GLOBAL VARIABLES

CACHE_DATA_DIRECTORY = os.path.join(MEDIA_DIRECTORY, 'cache')


# ## CLASSES

class MediaFile(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    md5 = DB.Column(DB.String(255), nullable=False)
    file_ext = DB.Column(DB.String(255), nullable=False)
    media_url = DB.Column(DB.String(255), nullable=False)
    expires = DB.Column(DB.DateTime(timezone=False), nullable=False)

    # ## Property methods

    @property
    def file_url(self):
        return image_server_url(self._partial_network_path, 'media')

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
