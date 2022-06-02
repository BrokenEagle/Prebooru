# APP/MODELS/UPLOAD_URL.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ## CLASSES

class UploadUrl(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    url = DB.Column(DB.String(255), nullable=False)
