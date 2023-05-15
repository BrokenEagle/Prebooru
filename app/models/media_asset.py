# APP/MODELS/MEDIA_ASSET.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel, BlobMD5


# ## CLASSES

class MediaAsset(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    md5 = DB.Column(BlobMD5(nullable=False), index=True, unique=True, nullable=False)
    width = DB.Column(DB.INTEGER, nullable=True)
    height = DB.Column(DB.INTEGER, nullable=True)
    size = DB.Column(DB.INTEGER, nullable=True)
    pixel_md5 = DB.Column(BlobMD5(nullable=True), nullable=True)
    duration = DB.Column(DB.REAL, nullable=True)
    audio = DB.Column(DB.BOOLEAN, nullable=True)
    file_ext = DB.Column(DB.TEXT, nullable=True)
