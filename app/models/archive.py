# APP/MODELS/ARCHIVE.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel, classproperty


# ## CLASSES

class ArchiveData(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    type = DB.Column(DB.String(255), nullable=False)
    data_key = DB.Column(DB.String(255), nullable=False)
    data = DB.Column(DB.JSON, nullable=False)
    expires = DB.Column(DB.DateTime(timezone=False), nullable=True)

    # ## Class properties

    @classproperty(cached=True)
    def searchable_attributes(cls):
        return [x for x in super().searchable_attributes if x not in ['data']]
