# APP/MODELS/DESCRIPTION.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ## CLASSES

class Description(JsonModel):
    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    body = DB.Column(DB.UnicodeText, nullable=False)

    # ## Relations
    # (MtM) artists [Artist]
    # (MtM) illusts [Illust]
