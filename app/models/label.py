# APP/MODELS/LABEL.PY

# ## PYTHON IMPORTS
from dataclasses import dataclass

# ## LOCAL IMPORTS
from .. import DB
from ..base_model import JsonModel


# ## CLASSES


@dataclass
class Label(JsonModel):
    # ## Declarations

    # #### JSON format
    id: int
    name: str

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.Unicode(255), nullable=False)

    # ## Class properties

    searchable_attributes = ['id', 'name']
