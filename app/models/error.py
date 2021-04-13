# APP/MODELS/ERROR.PY

# ## PYTHON IMPORTS
import datetime
from dataclasses import dataclass

# ## LOCAL IMPORTS
from .. import DB
from ..base_model import JsonModel


# ## CLASSES

@dataclass
class Error(JsonModel):
    # ## Declarations

    # #### JSON format
    id: int
    module: str
    message: str
    created: datetime.datetime.isoformat

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    module = DB.Column(DB.String(255), nullable=False)
    message = DB.Column(DB.UnicodeText, nullable=False)
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)

    # ## Class properties

    searchable_attributes = ['id', 'module', 'message', 'created']
