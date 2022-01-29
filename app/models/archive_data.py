# APP/MODELS/ARCHIVE_DATA.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ## CLASSES

class ArchiveData(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    type = DB.Column(DB.String(255), nullable=False)
    data_key = DB.Column(DB.String(255), nullable=False)
    data = DB.Column(DB.JSON, nullable=False)
    expires = DB.Column(DB.DateTime(timezone=False), nullable=True)

    basic_attributes = ['id', 'type', 'data_key', 'expires']
    relation_attributes = []
    searchable_attributes = basic_attributes + relation_attributes
    json_attributes = basic_attributes + ['data']
