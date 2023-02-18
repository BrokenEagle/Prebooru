# APP/MODELS/SITE_DATA.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import declared_attr

# ## PACKAGE IMPORTS
from config import USE_ENUMS

# ## LOCAL IMPORTS
from .. import DB
from ..enum_imports import site_data_type
from .base import JsonModel, EpochTimestamp, get_relation_definitions


# ## CLASSES

class SiteData(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    illust_id = DB.Column(DB.Integer, DB.ForeignKey('illust.id'), nullable=False, index=True)
    type, type_id, type_name, type_enum, type_filter, type_col =\
        get_relation_definitions(site_data_type, relname='type', relcol='id', colname='type_id',
                                 tblname='site_data', nullable=False)

    # ## Relations
    # (OtO) illust [Illust]

    # ## Instance properties

    def archive_dict(self):
        return {k: v for (k, v) in super().archive_dict().items() if k not in ['type', 'type_id']}

    # ## Class properties

    polymorphic_base = True

    # ## Private

    __mapper_args__ = {
        'polymorphic_identity': site_data_type.site_data.id,
        'polymorphic_on': type if USE_ENUMS else type_id,
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
        'polymorphic_identity': site_data_type.pixiv_data.id,
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
        'polymorphic_identity': site_data_type.twitter_data.id,
    }


# ## FUNCTIONS

def initialize():
    setattr(SiteData, 'polymorphic_classes', [PixivData, TwitterData])
