# APP/MODELS/API_DATA.PY

# ## PACKAGE IMPORTS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..enum_imports import api_data_type, site_descriptor
from .base import JsonModel, CompressedJSON, EpochTimestamp, get_relation_definitions


# ## CLASSES

class ApiData(JsonModel):
    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    type, type_id, type_name, type_enum, type_filter, type_col =\
        get_relation_definitions(api_data_type, relname='type', relcol='id', colname='type_id',
                                 tblname='api_data', nullable=False)
    site, site_id, site_name, site_enum, site_filter, site_col =\
        get_relation_definitions(site_descriptor, relname='site', relcol='id', colname='site_id',
                                 tblname='api_data', nullable=False)
    data_id = DB.Column(DB.Integer, nullable=False)
    data = DB.Column(CompressedJSON(), nullable=False)
    expires = DB.Column(EpochTimestamp(nullable=False), nullable=False)

    # ## Class properties

    @classproperty(cached=True)
    def searchable_attributes(cls):
        return [x for x in super().searchable_attributes if x not in ['data']]
