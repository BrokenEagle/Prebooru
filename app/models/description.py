# APP/MODELS/DESCRIPTION.PY

# ## PYTHON IMPORTS
from dataclasses import dataclass

# ## LOCAL IMPORTS
from .. import DB
from ..base_model import JsonModel


# ## CLASSES

@dataclass
class Description(JsonModel):
    # ## Declarations

    # #### JSON format
    id: int
    body: str

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    body = DB.Column(DB.UnicodeText, nullable=False)

    # ## Class properties

    searchable_attributes = ['id', 'body']
