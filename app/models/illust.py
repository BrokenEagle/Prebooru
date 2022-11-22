# APP/MODELS/ILLUST.PY

# ## EXTERNAL LINKS
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..logical.sites import SiteDescriptor
from .tag import SiteTag
from .illust_url import IllustUrl
from .site_data import SiteData
from .description import Description
from .notation import Notation
from .pool_element import PoolIllust
from .base import JsonModel, IntEnum, EpochTimestamp, secondarytable, polymorphic_accessor_factory


# ## GLOBAL VARIABLES

# Many-to-many tables

IllustTags = secondarytable(
    'illust_tags',
    DB.Column('illust_id', DB.Integer, DB.ForeignKey('illust.id'), primary_key=True),
    DB.Column('tag_id', DB.Integer, DB.ForeignKey('tag.id'), primary_key=True),
)

IllustCommentaries = secondarytable(
    'illust_commentaries',
    DB.Column('illust_id', DB.Integer, DB.ForeignKey('illust.id'), primary_key=True),
    DB.Column('description_id', DB.Integer, DB.ForeignKey('description.id'), primary_key=True),
)

IllustNotations = secondarytable(
    'illust_notations',
    DB.Column('illust_id', DB.Integer, DB.ForeignKey('illust.id'), primary_key=True),
    DB.Column('notation_id', DB.Integer, DB.ForeignKey('notation.id'), primary_key=True),
    DB.Index(None, 'notation_id', 'illust_id'),
)


# ## CLASSES

class Illust(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    site = DB.Column(IntEnum(SiteDescriptor), nullable=False)
    site_illust_id = DB.Column(DB.Integer, nullable=False)
    site_created = DB.Column(EpochTimestamp(nullable=True), nullable=True)
    artist_id = DB.Column(DB.Integer, DB.ForeignKey('artist.id'), nullable=False, index=True)
    pages = DB.Column(DB.Integer, nullable=False)
    score = DB.Column(DB.Integer, nullable=False)
    active = DB.Column(DB.Boolean, nullable=False)
    created = DB.Column(EpochTimestamp(nullable=False), nullable=False)
    updated = DB.Column(EpochTimestamp(nullable=False), nullable=False)

    # ## Relationships
    _commentaries = DB.relationship(Description, secondary=IllustCommentaries, lazy=True, uselist=True,
                                    backref=DB.backref('illusts', lazy=True, uselist=True))
    _tags = DB.relationship(SiteTag, secondary=IllustTags, lazy=True, uselist=True,
                            backref=DB.backref('illusts', lazy=True, uselist=True))
    urls = DB.relationship(IllustUrl, lazy=True, uselist=True, cascade="all, delete",
                           backref=DB.backref('illust', lazy=True, uselist=False))
    site_data = DB.relationship(SiteData, lazy=True, uselist=False, cascade="all, delete",
                                backref=DB.backref('illust', lazy=True, uselist=False))
    notations = DB.relationship(Notation, secondary=IllustNotations, lazy=True, uselist=True, cascade='all,delete',
                                backref=DB.backref('illust', uselist=False, lazy=True))
    # Pool elements must be deleted individually, since pools will need to be reordered/recounted
    _pools = DB.relationship(PoolIllust, lazy=True, uselist=True,
                             backref=DB.backref('item', lazy=True, uselist=False))
    # (OtO) artist [Artist]

    # ## Association proxies
    tags = association_proxy('_tags', 'name')
    commentaries = association_proxy('_commentaries', 'body')
    pools = association_proxy('_pools', 'pool')
    _posts = association_proxy('urls', 'post')
    boorus = association_proxy('artist', 'boorus')
    title = association_proxy('site_data', 'title', getset_factory=polymorphic_accessor_factory)
    retweets = association_proxy('site_data', 'retweets', getset_factory=polymorphic_accessor_factory)
    replies = association_proxy('site_data', 'replies', getset_factory=polymorphic_accessor_factory)
    quotes = association_proxy('site_data', 'quotes', getset_factory=polymorphic_accessor_factory)
    bookmarks = association_proxy('site_data', 'bookmarks', getset_factory=polymorphic_accessor_factory)
    site_updated = association_proxy('site_data', 'site_updated', getset_factory=polymorphic_accessor_factory)
    site_uploaded = association_proxy('site_data', 'site_uploaded', getset_factory=polymorphic_accessor_factory)

    # ## Instance properties

    @memoized_property
    def ordered_urls(self):
        return sorted(self.urls, key=lambda x: x.order)

    @memoized_property
    def posts(self):
        return [post for post in self._posts if post is not None]

    @property
    def site_domain(self):
        return self.site.domain

    @memoized_property
    def type(self):
        if self.site.source.illust_has_videos(self):
            return 'video'
        elif self.site.source.illust_has_images(self):
            return 'image'
        else:
            return 'unknown'

    def delete(self):
        pools = [pool for pool in self.pools]
        DB.session.delete(self)
        DB.session.commit()
        if len(pools) > 0:
            for pool in pools:
                pool._elements.reorder()
            DB.session.commit()

    # ## Class properties

    site_enum = SiteDescriptor

    @classproperty(cached=True)
    def json_attributes(cls):
        return super().json_attributes + ['urls', 'tags', 'commentaries', 'site_data']

    # ## Private

    __table_args__ = (DB.UniqueConstraint('site_illust_id', 'site'),)


# ## INITIALIZATION

def initialize():
    from .artist import Artist
    # Access the opposite side of the relationship to force the back reference to be generated
    Artist.illusts.property._configure_started
    Illust.set_relation_properties()
