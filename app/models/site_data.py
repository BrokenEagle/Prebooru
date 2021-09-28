# APP/MODELS/SITE_DATA.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import declared_attr

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ## CLASSES

class SiteData(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    illust_id = DB.Column(DB.Integer, DB.ForeignKey('illust.id'), nullable=False)
    type = DB.Column(DB.String(50))

    basic_attributes = ['id', 'illust_id', 'type']
    json_attributes = basic_attributes

    # ## Private

    __tablename__ = 'site_data'
    __mapper_args__ = {
        'polymorphic_identity': 'site_data',
        "polymorphic_on": type
    }


class PixivData(SiteData):
    # ## Declarations

    # #### Columns
    site_uploaded = DB.Column(DB.DateTime(timezone=False), nullable=True)
    site_updated = DB.Column(DB.DateTime(timezone=False), nullable=True)
    title = DB.Column(DB.UnicodeText, nullable=True)
    bookmarks = DB.Column(DB.Integer, nullable=True)
    views = DB.Column(DB.Integer, nullable=True)

    # #### Declared columns
    #
    # Polymorphic models with columns that conflict must be declared like this
    @declared_attr
    def replies(cls):
        return SiteData.__table__.c.get('replies', DB.Column(DB.Integer, nullable=True))

    # ## Class properties

    basic_attributes = SiteData.basic_attributes + ['site_uploaded', 'site_updated', 'title', 'bookmarks', 'views']
    json_attributes = basic_attributes

    # ## Private

    __tablename__ = 'pixiv_data'
    __mapper_args__ = {
        'polymorphic_identity': 'pixiv_data',
    }


class TwitterData(SiteData):
    # ## Declarations

    # #### Columns
    retweets = DB.Column(DB.Integer, nullable=True)
    quotes = DB.Column(DB.Integer, nullable=True)

    # #### Declared columns
    #
    # Polymorphic models with columns that conflict must be declared like this
    @declared_attr
    def replies(cls):
        return SiteData.__table__.c.get('replies', DB.Column(DB.Integer, nullable=True))

    # ## Class properties

    basic_attributes = SiteData.basic_attributes + ['retweets', 'replies', 'quotes']
    json_attributes = basic_attributes

    # ## Private

    __tablename__ = 'twitter_data'
    __mapper_args__ = {
        'polymorphic_identity': 'twitter_data',
    }
