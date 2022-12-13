# APP/MODELS/POOL_ELEMENT.PY

# ## LOCAL IMPORTS
from .. import DB
from ..enum_imports import danbooru_asset_model
from .base import JsonModel, get_relation_definitions


# ## CLASSES

class DanbooruAsset(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    asset_id = DB.Column(DB.Integer, nullable=False)
    model, model_id, model_enum, model_filter =\
        get_relation_definitions(danbooru_asset_model, relname='model', relcol='id', colname='model_id',
                                 tblname='danbooru_asset', nullable=False)
