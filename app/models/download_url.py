# APP/MODELS/DOWNLOAD_URL.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ## CLASSES

class DownloadUrl(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    url = DB.Column(DB.TEXT, nullable=False)
    download_id = DB.Column(DB.Integer, DB.ForeignKey('download.id'), nullable=False)

    # ## Relations
    # (MtO) download [Download]


# ## INITIALIZATION

def initialize():
    DB.Index(None, DownloadUrl.download_id, unique=False)
