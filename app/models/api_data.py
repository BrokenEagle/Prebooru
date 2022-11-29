# APP/MODELS/API_DATA.PY

# ## PACKAGE IMPORTS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..enum_imports import api_data_type, site_descriptor
from .base import JsonModel, IntEnum, CompressedJSON, EpochTimestamp, get_relation_definitions


# ## CLASSES

class ApiData(JsonModel):
    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    type, type_id, type_enum, type_filter = get_relation_definitions(api_data_type, 'type_id', 'type', 'id', 'api_data', nullable=False)
    site, site_id, site_enum, site_filter  = get_relation_definitions(site_descriptor, 'site_id', 'site', 'id', 'api_data', nullable=False)
    data_id = DB.Column(DB.Integer, nullable=False)
    data = DB.Column(CompressedJSON(), nullable=False)
    expires = DB.Column(EpochTimestamp(nullable=False), nullable=False)

    # ## Class properties

    @classproperty(cached=True)
    def searchable_attributes(cls):
        return [x for x in super().searchable_attributes if x not in ['data']]
