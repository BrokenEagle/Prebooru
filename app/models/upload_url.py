# APP/MODELS/UPLOAD_URL.PY

# ## PYTHON IMPORTS
from dataclasses import dataclass

# ## LOCAL IMPORTS
from .. import DB
from ..base_model import JsonModel


# ## CLASSES

@dataclass
class UploadUrl(JsonModel):
    # ## Declarations

    # #### JSON format
    id: int
    url: str

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    url = DB.Column(DB.String(255), nullable=False)

    # ## Class properties

    searchable_attributes = ['id', 'url']
