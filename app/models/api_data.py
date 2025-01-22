# APP/MODELS/API_DATA.PY

# ## PACKAGE IMPORTS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from .model_enums import ApiDataType, SiteDescriptor
from .base import JsonModel, IntEnum, CompressedJSON, EpochTimestamp, register_enum_column


# ## CLASSES

class ApiData(JsonModel):
    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    type_id = DB.Column(IntEnum, DB.ForeignKey('api_data_type.id'), nullable=False)
    site_id = DB.Column(IntEnum, DB.ForeignKey('site_descriptor.id'), nullable=False)
    data_id = DB.Column(DB.Integer, nullable=False)
    data = DB.Column(CompressedJSON(), nullable=False)
    expires = DB.Column(EpochTimestamp(nullable=False), nullable=False)

    # ## Class properties

    @property
    def source(self):
        from ..logical.sources import source_by_site_name
        return source_by_site_name(self.site.name)

    @classproperty(cached=True)
    def searchable_attributes(cls):
        return [x for x in super().searchable_attributes if x not in ['data']]


# ## Initialize

def initialize():
    register_enum_column(ApiData, ApiDataType, 'type')
    register_enum_column(ApiData, SiteDescriptor, 'site')
