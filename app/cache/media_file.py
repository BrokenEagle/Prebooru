# APP/CACHE/MEDIA_FILE.PY

# ## LOCAL IMPORTS
from .. import DB
from ..storage import CACHE_DATA_DIRECTORY, CacheNetworkUrlpath


# ## CLASSES

class MediaFile(DB.Model):
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
        return CacheNetworkUrlpath() + self.md5 + '.' + self.file_ext

    @property
    def file_path(self):
        return CACHE_DATA_DIRECTORY + self.md5 + '.' + self.file_ext
