# APP/MODELS/POOL_ELEMENT.PY

# ## LOCAL IMPORTS
from .. import DB
from ..enum_imports import danbooru_asset_model
from .base import JsonModel, get_relation_definitions


# ## GLOBAL VARIABLES

# IS NULL produces a boolean, which is evaluated internally as either a 1 (truth) or 0 (false)
SINGLE_FOREIGN_KEY_NOT_NULL = "((booru_id IS NULL) + (artist_id IS NULL) + (illust_id IS NULL) + (post_id IS NULL)) = 3"


# ## CLASSES

class DanbooruAsset(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    asset_id = DB.Column(DB.Integer, nullable=False)
    model, model_id, model_enum, model_filter =\
        get_relation_definitions(danbooru_asset_model, relname='model', relcol='id', colname='model_id',
                                 tblname='danbooru_asset', nullable=False)
    booru_id = DB.Column(DB.Integer, DB.ForeignKey('booru.id'), nullable=True)
    artist_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=True)
    illust_id = DB.Column(DB.Integer, DB.ForeignKey('illust.id'), nullable=True)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=True)

    __table_args__ = (
        DB.CheckConstraint(
            SINGLE_FOREIGN_KEY_NOT_NULL,
            name="null_check"),
    )
