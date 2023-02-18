# APP/MODELS/ILLUST.PY

# ## EXTERNAL LINKS
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..enum_imports import site_descriptor
from .tag import SiteTag, site_tag_creator
from .illust_url import IllustUrl
from .site_data import SiteData
from .description import Description, description_creator
from .notation import Notation
from .pool_element import PoolIllust
from .base import JsonModel, EpochTimestamp, secondarytable, polymorphic_accessor_factory, get_relation_definitions


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


# ## CLASSES

class Illust(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    site, site_id, site_name, site_enum, site_filter, site_col =\
        get_relation_definitions(site_descriptor, relname='site', relcol='id', colname='site_id',
                                 tblname='illust', nullable=False)
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
    notations = DB.relationship(Notation, lazy=True, uselist=True, cascade='all,delete',
                                backref=DB.backref('illust', uselist=False, lazy=True))
    # Pool elements must be deleted individually, since pools will need to be reordered/recounted
    _pools = DB.relationship(PoolIllust, lazy=True, uselist=True,
                             backref=DB.backref('item', lazy=True, uselist=False))
    # (OtO) artist [Artist]

    # ## Association proxies
    tags = association_proxy('_tags', 'name', creator=site_tag_creator)
    commentaries = association_proxy('_commentaries', 'body', creator=description_creator)
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

    def urls_paginate(self, page=None, per_page=None, options=None):
        def _get_options(options):
            if options is None:
                return (lazyload('*'),)
            if type(options) is tuple:
                return options
            return (options,)
        query = self._urls_query
        query = query.options(*_get_options(options))
        query = query.order_by(IllustUrl.order)
        return query.count_paginate(per_page=per_page, page=page)

    @memoized_property
    def posts(self):
        return [post for post in self._posts if post is not None]

    @property
    def type(self):
        if self.has_images and self.has_videos:
            return 'mixed'
        if self.has_images:
            return 'image'
        if self.has_videos:
            return 'video'
        return 'unknown'

    @memoized_property
    def has_images(self):
        return any(illust_url.type == 'image' for illust_url in self.urls)

    @memoized_property
    def has_videos(self):
        return any(illust_url.type == 'video' for illust_url in self.urls)

    @property
    def site_domain(self):
        return self.site.domain

    def delete(self):
        pools = [pool for pool in self.pools]
        DB.session.delete(self)
        DB.session.commit()
        if len(pools) > 0:
            for pool in pools:
                pool._elements.reorder()
            DB.session.commit()

    def archive_dict(self):
        return {k: v for (k, v) in super().archive_dict().items() if k not in ['site', 'site_id']}

    # ## Class properties

    @classproperty(cached=True)
    def json_attributes(cls):
        return super().json_attributes + ['urls', 'tags', 'commentaries', 'site_data']

    # ## Private

    @property
    def _urls_query(self):
        return IllustUrl.query.filter_by(illust_id=self.id)

    __table_args__ = (
        DB.UniqueConstraint('site_illust_id', 'site_id'),
    )


# ## INITIALIZATION

def initialize():
    from .artist import Artist
    # Access the opposite side of the relationship to force the back reference to be generated
    Artist.illusts.property._configure_started
    Illust.set_relation_properties()
