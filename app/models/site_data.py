# APP/MODELS/SITE_DATA.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass
from sqlalchemy.orm import declared_attr

# ##LOCAL IMPORTS
from .. import DB
from ..base_model import JsonModel, DateTimeOrNull, IntOrNone


# ##GLOBAL VARIABLES


@dataclass
class SiteData(JsonModel):
    __tablename__ = 'site_data'
    id: int
    illust_id: int
    type: str
    id = DB.Column(DB.Integer, primary_key=True)
    illust_id = DB.Column(DB.Integer, DB.ForeignKey('illust.id'), nullable=False)
    type = DB.Column(DB.String(50))

    __mapper_args__ = {
        'polymorphic_identity': 'site_data',
        "polymorphic_on": type
    }


@dataclass
class PixivData(SiteData):
    __tablename__ = 'pixiv_data'
    site_uploaded: DateTimeOrNull
    site_updated: DateTimeOrNull
    title: str
    bookmarks: IntOrNone
    replies: IntOrNone
    views: IntOrNone
    site_uploaded = DB.Column(DB.DateTime(timezone=False), nullable=True)
    site_updated = DB.Column(DB.DateTime(timezone=False), nullable=True)
    title = DB.Column(DB.UnicodeText, nullable=True)
    bookmarks = DB.Column(DB.Integer, nullable=True)
    views = DB.Column(DB.Integer, nullable=True)

    @declared_attr
    def replies(cls):
        return SiteData.__table__.c.get('replies', DB.Column(DB.Integer, nullable=True))

    __mapper_args__ = {
        'polymorphic_identity': 'pixiv_data',
    }


@dataclass
class TwitterData(SiteData):
    __tablename__ = 'twitter_data'
    retweets: IntOrNone
    replies: IntOrNone
    quotes: IntOrNone
    retweets = DB.Column(DB.Integer, nullable=True)
    quotes = DB.Column(DB.Integer, nullable=True)

    @declared_attr
    def replies(cls):
        return SiteData.__table__.c.get('replies', DB.Column(DB.Integer, nullable=True))

    __mapper_args__ = {
        'polymorphic_identity': 'twitter_data',
    }
