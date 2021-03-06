# APP/MODELS/LABEL.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ## CLASSES

class Label(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.Unicode(255), nullable=False)
