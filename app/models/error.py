# APP/MODELS/ERROR.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel, NormalizedDatetime


# ## CLASSES

class Error(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    module = DB.Column(DB.String(255), nullable=False)
    message = DB.Column(DB.UnicodeText, nullable=False)
    created = DB.Column(NormalizedDatetime(), nullable=False)
