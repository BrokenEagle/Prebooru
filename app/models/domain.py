# APP/CACHE/DOMAIN.PY

# ##LOCAL IMPORTS
from .. import DB
from ..base_model import JsonModel


# ## CLASSES

class Domain(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String(255), nullable=False)
    redirector = DB.Column(DB.Boolean, nullable=False)
