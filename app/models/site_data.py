# APP/MODELS/SITE_DATA.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import declared_attr

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel, NormalizedDatetime


# ## CLASSES

class SiteData(JsonModel):
    # ## Declarations

    # ## Class attributes

    polymorphic_base = True

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    illust_id = DB.Column(DB.Integer, DB.ForeignKey('illust.id'), nullable=False)
    type = DB.Column(DB.String(50))

    # ## Private

    __tablename__ = 'site_data'
    __mapper_args__ = {
        'polymorphic_identity': 'site_data',
        "polymorphic_on": type
    }


class PixivData(SiteData):
    # ## Declarations

    # ## Class attributes

    polymorphic_base = False

    # #### Columns
    site_uploaded = DB.Column(NormalizedDatetime(), nullable=True)
    site_updated = DB.Column(NormalizedDatetime(), nullable=True)
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

    __tablename__ = 'pixiv_data'
    __mapper_args__ = {
        'polymorphic_identity': 'pixiv_data',
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

    __tablename__ = 'twitter_data'
    __mapper_args__ = {
        'polymorphic_identity': 'twitter_data',
    }


# ## FUNCTIONS

def initialize():
    setattr(SiteData, 'polymorphic_classes', [PixivData, TwitterData])
