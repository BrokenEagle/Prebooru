# APP/MODELS/API_DATA.PY

# ## PACKAGE IMPORTS
from utility.obj import classproperty, memoized_classproperty
from utility.data import swap_list_values, list_difference

# ## LOCAL IMPORTS
from .model_enums import ApiDataType, SiteDescriptor
from .base import JsonModel, integer_column, enum_column, compressed_json_column, timestamp_column,\
    register_enum_column


# ## CLASSES

class ApiData(JsonModel):
    # #### Columns
    id = integer_column(primary_key=True)
    type_id = enum_column(foreign_key='api_data_type.id', nullable=False)
    site_id = enum_column(foreign_key='site_descriptor.id', nullable=False)
    data_id = integer_column(nullable=False)
    data = compressed_json_column(nullable=False)
    expires = timestamp_column(nullable=False)

    # ## Class properties

    @memoized_classproperty
    def searchable_attributes(cls):
        return list_difference(super().searchable_attributes, ['data'])

    @memoized_classproperty
    def repr_attributes(cls):
        mapping = {
            'type_id': ('type', 'type_name'),
            'site_id': ('site', 'site_name'),
        }
        return swap_list_values(super().repr_attributes, mapping)

    @classproperty
    def json_attributes(cls):
        return cls.repr_attributes


# ## Initialize

def initialize():
    register_enum_column(ApiData, ApiDataType, 'type')
    register_enum_column(ApiData, SiteDescriptor, 'site')
