# APP/MODELS/MEDIA_FILE.PY

# ## PYTHON IMPORTS
import os

# ## PACKAGE IMPORTS
from config import MEDIA_DIRECTORY
from utility.obj import memoized_classproperty

# ## LOCAL IMPORTS
from .base import JsonModel, integer_column, text_column, md5_column, timestamp_column, image_server_url


# ## GLOBAL VARIABLES

CACHE_DATA_DIRECTORY = os.path.join(MEDIA_DIRECTORY, 'cache')


# ## CLASSES

class MediaFile(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    md5 = md5_column(nullable=False)
    file_ext = text_column(nullable=False)
    media_url = text_column(nullable=False)
    expires = timestamp_column(nullable=False)

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

    @memoized_classproperty
    def json_attributes(cls):
        return super().json_attributes + ['file_url']
