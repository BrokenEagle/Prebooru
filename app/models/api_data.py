# APP/MODELS/API_DATA.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel, NormalizedDatetime, classproperty


# ## CLASSES

class ApiData(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    type = DB.Column(DB.String(255), nullable=False)
    site_id = DB.Column(DB.Integer, nullable=False)
    data_id = DB.Column(DB.Integer, nullable=False)
    data = DB.Column(DB.JSON, nullable=False)
    expires = DB.Column(NormalizedDatetime(), nullable=False)

    # ## Class properties

    @classproperty(cached=True)
    def searchable_attributes(cls):
        return [x for x in super().searchable_attributes if x not in ['data']]
