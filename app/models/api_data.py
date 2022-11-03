# APP/MODELS/API_DATA.PY

# ## PYTHON IMPORTS
import enum

# ## PACKAGE IMPORTS
from utility.obj import AttrEnum, classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..logical.sites import Site
from .base import JsonModel, IntEnum, CompressedJSON, EpochTimestamp


# ## CLASSES

class ApiDataType(AttrEnum):
    illust = enum.auto()
    artist = enum.auto()
    profile = enum.auto()
    page = enum.auto()


class ApiData(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    type = DB.Column(IntEnum(ApiDataType), nullable=False)
    site_id = DB.Column(IntEnum(Site), nullable=False)
    data_id = DB.Column(DB.Integer, nullable=False)
    data = DB.Column(CompressedJSON(), nullable=False)
    expires = DB.Column(EpochTimestamp(nullable=False), nullable=False)

    # ## Class properties

    type_enum = ApiDataType
    site_id_enum = Site

    @classproperty(cached=True)
    def searchable_attributes(cls):
        return [x for x in super().searchable_attributes if x not in ['data']]
