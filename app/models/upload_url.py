# APP/MODELS/UPLOAD_URL.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ## CLASSES

class UploadUrl(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    url = DB.Column(DB.TEXT, nullable=False)
    upload_id = DB.Column(DB.Integer, DB.ForeignKey('upload.id'), nullable=False)

    # ## Relations
    # (MtO) upload [Upload]


# ## INITIALIZATION

def initialize():
    DB.Index(None, UploadUrl.upload_id, unique=False)
