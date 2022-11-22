# APP/MODELS/API_DATA.PY

# ## PYTHON IMPORTS
import enum

# ## PACKAGE IMPORTS
from utility.obj import AttrEnum, classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..logical.sites import SiteDescriptorEnum
from .base import JsonModel, IntEnum, CompressedJSON, EpochTimestamp


# ## CLASSES

class ApiDataTypeEnum(AttrEnum):
    illust = enum.auto()
    artist = enum.auto()
    profile = enum.auto()
    page = enum.auto()


class ApiData(JsonModel):
    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    type = DB.Column(IntEnum(ApiDataTypeEnum), nullable=False)
    site = DB.Column(IntEnum(SiteDescriptorEnum), nullable=False)
    data_id = DB.Column(DB.Integer, nullable=False)
    data = DB.Column(CompressedJSON(), nullable=False)
    expires = DB.Column(EpochTimestamp(nullable=False), nullable=False)

    # ## Class properties

    type_enum = ApiDataTypeEnum
    site_enum = SiteDescriptorEnum

    @classproperty(cached=True)
    def searchable_attributes(cls):
        return [x for x in super().searchable_attributes if x not in ['data']]
