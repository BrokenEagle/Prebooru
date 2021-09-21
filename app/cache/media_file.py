# APP/CACHE/MEDIA_FILE.PY

# ## PYTHON IMPORTS
import os

# ## LOCAL IMPORTS
from .. import DB
from ..base_model import JsonModel, image_server_url
from ..config import IMAGE_DIRECTORY


# ## GLOBAL VARIABLES

CACHE_DATA_DIRECTORY = os.path.join(IMAGE_DIRECTORY, 'cache')


# ## CLASSES

class MediaFile(JsonModel):
    # ## Declarations

    # #### SqlAlchemy
    __bind_key__ = 'cache'

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    md5 = DB.Column(DB.String(255), nullable=False)
    file_ext = DB.Column(DB.String(255), nullable=False)
    media_url = DB.Column(DB.String(255), nullable=False)
    expires = DB.Column(DB.DateTime(timezone=False), nullable=False)

    # ## Property methods

    @property
    def file_url(self):
        return image_server_url(self._partial_network_path)

    @property
    def file_path(self):
        return os.path.join(CACHE_DATA_DIRECTORY, self._partial_file_path)

    @property
    def _partial_network_path(self):
        return 'cache/%s.%s' % (self.md5, self.file_ext)

    @property
    def _partial_file_path(self):
        return '%s.%s' % (self.md5, self.file_ext)
