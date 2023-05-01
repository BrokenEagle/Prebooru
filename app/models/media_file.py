# APP/MODELS/MEDIA_FILE.PY

# ## PYTHON IMPORTS
import os

# ## EXTERNAL IMPORTS
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from config import MEDIA_DIRECTORY
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from .media_asset import MediaAsset
from .base import JsonModel, BlobMD5, EpochTimestamp, image_server_url


# ## GLOBAL VARIABLES

CACHE_DATA_DIRECTORY = os.path.join(MEDIA_DIRECTORY, 'cache')


# ## CLASSES

class MediaFile(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    #md5 = DB.Column(BlobMD5(nullable=False), nullable=False)
    #file_ext = DB.Column(DB.String(255), nullable=False)
    media_url = DB.Column(DB.String(255), nullable=False)
    expires = DB.Column(EpochTimestamp(nullable=False), nullable=False)
    media_asset_id = DB.Column(DB.INTEGER, DB.ForeignKey('media_asset.id'), nullable=False)

    # ## Relationships
    media = DB.relationship(MediaAsset, lazy='selectin', uselist=False,
                            backref=DB.backref('media_file', lazy=True, uselist=False))

    # ## Association proxies
    md5 = association_proxy('media', 'md5')
    file_ext = association_proxy('media', 'file_ext')

    # ## Class properties

    @classproperty(cached=True)
    def json_attributes(cls):
        return super().json_attributes + ['file_url']
