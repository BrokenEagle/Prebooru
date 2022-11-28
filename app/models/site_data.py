# APP/MODELS/SITE_DATA.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import declared_attr

# ## LOCAL IMPORTS
from .. import DB
from ..logical.enums import SiteDataTypeEnum
from .base import JsonModel, IntEnum, EpochTimestamp


# ## CLASSES

class SiteData(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    illust_id = DB.Column(DB.Integer, DB.ForeignKey('illust.id'), nullable=False, index=True)
    type = DB.Column(IntEnum(SiteDataTypeEnum), nullable=False)

    # ## Relations
    # (OtO) illust [Illust]

    # ## Class properties

    polymorphic_base = True
    type_enum = SiteDataTypeEnum

    # ## Private

    __mapper_args__ = {
        'polymorphic_identity': SiteDataTypeEnum.site_data,
        'polymorphic_on': type,
    }


class PixivData(SiteData):
    # ## Columns
    site_uploaded = DB.Column(EpochTimestamp(nullable=True), nullable=True)
    site_updated = DB.Column(EpochTimestamp(nullable=True), nullable=True)
    title = DB.Column(DB.UnicodeText, nullable=True)
    bookmarks = DB.Column(DB.Integer, nullable=True)
    views = DB.Column(DB.Integer, nullable=True)

    # ## Declared columns
    #
    # Polymorphic models with columns that conflict must be declared like this
    @declared_attr
    def replies(self):
        return SiteData.__table__.c.get('replies', DB.Column(DB.Integer, nullable=True))

    # ## Class properties

    polymorphic_base = False

    # ## Private

    __mapper_args__ = {
        'polymorphic_identity': SiteDataTypeEnum.pixiv_data,
    }


class TwitterData(SiteData):
    # ## Columns
    retweets = DB.Column(DB.Integer, nullable=True)
    quotes = DB.Column(DB.Integer, nullable=True)

    # ## Declared columns
    #
    # Polymorphic models with columns that conflict must be declared like this
    @declared_attr
    def replies(self):
        return SiteData.__table__.c.get('replies', DB.Column(DB.Integer, nullable=True))

    # ## Class properties

    polymorphic_base = False

    # ## Private

    __mapper_args__ = {
        'polymorphic_identity': SiteDataTypeEnum.twitter_data,
    }


# ## FUNCTIONS

def initialize():
    setattr(SiteData, 'polymorphic_classes', [PixivData, TwitterData])
