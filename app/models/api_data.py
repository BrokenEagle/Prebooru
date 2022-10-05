# APP/MODELS/API_DATA.PY

# ## PYTHON IMPORTS
import enum

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel, ModelEnum, IntEnum, CompressedJSON, NormalizedDatetime, classproperty


# ## CLASSES

class ApiDataType(ModelEnum):
    illust = enum.auto()
    artist = enum.auto()
    profile = enum.auto()
    page = enum.auto()


class ApiData(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    type = DB.Column(IntEnum(ApiDataType), nullable=False)
    site_id = DB.Column(DB.Integer, nullable=False)
    data_id = DB.Column(DB.Integer, nullable=False)
    data = DB.Column(CompressedJSON(), nullable=False)
    expires = DB.Column(NormalizedDatetime(), nullable=False)

    # ## Class properties

    type_enum = ApiDataType

    @classproperty(cached=True)
    def searchable_attributes(cls):
        return [x for x in super().searchable_attributes if x not in ['data']]
