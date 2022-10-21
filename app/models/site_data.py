# APP/MODELS/SITE_DATA.PY

# ## PYTHON IMPORTS
import enum

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import declared_attr

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel, ModelEnum, IntEnum, EpochTimestamp


# ## CLASSES

class SiteDataType(ModelEnum):
    site_data = -1  # This should never actually be set
    pixiv_data = enum.auto()
    twitter_data = enum.auto()


class SiteData(JsonModel):
    # ## Declarations

    # ## Class attributes

    polymorphic_base = True

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    illust_id = DB.Column(DB.Integer, DB.ForeignKey('illust.id'), nullable=False, index=True)
    type = DB.Column(IntEnum(SiteDataType), nullable=False)

    # ## Class properties

    type_enum = SiteDataType

    # ## Private

    __mapper_args__ = {
        'polymorphic_identity': SiteDataType.site_data,
        'polymorphic_on': type,
    }


class PixivData(SiteData):
    # ## Declarations

    # ## Class attributes

    polymorphic_base = False

    # #### Columns
    site_uploaded = DB.Column(EpochTimestamp(nullable=True), nullable=True)
    site_updated = DB.Column(EpochTimestamp(nullable=True), nullable=True)
    title = DB.Column(DB.UnicodeText, nullable=True)
    bookmarks = DB.Column(DB.Integer, nullable=True)
    views = DB.Column(DB.Integer, nullable=True)

    # #### Declared columns
    #
    # Polymorphic models with columns that conflict must be declared like this
    @declared_attr
    def replies(self):
        return SiteData.__table__.c.get('replies', DB.Column(DB.Integer, nullable=True))

    # ## Private

    __mapper_args__ = {
        'polymorphic_identity': SiteDataType.pixiv_data,
    }


class TwitterData(SiteData):
    # ## Declarations

    # ## Class attributes

    polymorphic_base = False

    # #### Columns
    retweets = DB.Column(DB.Integer, nullable=True)
    quotes = DB.Column(DB.Integer, nullable=True)

    # #### Declared columns
    #
    # Polymorphic models with columns that conflict must be declared like this
    @declared_attr
    def replies(self):
        return SiteData.__table__.c.get('replies', DB.Column(DB.Integer, nullable=True))

    # ## Private

    __mapper_args__ = {
        'polymorphic_identity': SiteDataType.twitter_data,
    }


# ## FUNCTIONS

def initialize():
    setattr(SiteData, 'polymorphic_classes', [PixivData, TwitterData])
