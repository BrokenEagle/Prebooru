# APP/MODELS/ILLUST.PY

# ## EXTERNAL LINKS
from sqlalchemy.util import memoized_property
from sqlalchemy.orm import lazyload
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..enum_imports import site_descriptor
from ..logical.batch_loader import selectinload_batch_primary
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

    @property
    def site_illust_id_str(self):
        return str(self.site_illust_id)

    def urls_paginate(self, page=None, per_page=None, options=None, url_type=None):
        def _get_options(options):
            if options is None:
                return (lazyload('*'),)
            if type(options) is tuple:
                return options
            return (options,)
        query = self._urls_query
        if url_type == 'posted':
            query = query.filter(IllustUrl.post_id.is_not(None))
        elif url_type == 'unposted':
            query = query.filter(IllustUrl.post_id.is_(None))
        query = query.options(*_get_options(options))
        query = query.order_by(IllustUrl.order)
        return query.count_paginate(per_page=per_page, page=page)

    @memoized_property
    def active_urls(self):
        return [url for url in self.urls if url.post_id is not None]

    @memoized_property
    def posts(self):
        self._populate_posts()
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

    @property
    def source(self):
        return self.site.source

    @memoized_property
    def has_images(self):
        return any(illust_url.type == 'image' for illust_url in self.urls)

    @memoized_property
    def has_videos(self):
        return any(illust_url.type == 'video' for illust_url in self.urls)

    @property
    def primary_url(self):
        return self.source.get_primary_url(self)

    @property
    def secondary_url(self):
        return self.source.get_secondary_url(self)

    @property
    def site_domain(self):
        return self.site.domain

    @property
    def shortlink(self):
        return "%s #%d" % (illust.site.name.lower(), illust.site_illust_id)

    @property
    def key(self):
        return '%s-%d' % (self.site.name, self.site_illust_id)

    def get_url_by_key(self, key):
        return next((illust_url for illust_url in self.urls if illust_url.key == key), None)

    def attach_post_by_link_key(self, link_key):
        from .post import Post
        post = Post.query.filter_by(md5=link_key['md5']).one_or_none()
        if post is not None:
            illust_url = self.get_url_by_key(link_key['key'])
            if illust_url is not None:
                illust_url.post = post
                return True
        return False

    def delete(self):
        pools = [pool for pool in self.pools]
        DB.session.delete(self)
        DB.session.commit()
        if len(pools) > 0:
            for pool in pools:
                pool._elements.reorder()
            DB.session.commit()

    # ## Class properties

    @classmethod
    def find_by_key(cls, key):
        site_name, site_illust_id_str = key.split('-')
        enum_filter = cls.site_filter('name', '__eq__', site_name)
        id_filter = cls.site_illust_id == int(site_illust_id_str)
        return cls.query.enum_join(cls.site_enum)\
                        .filter(enum_filter, id_filter)\
                        .one_or_none()

    @classmethod
    def find_rel_by_key(cls, rel, key, value):
        from .artist import Artist
        from .post import Post
        if rel == 'artist':
            site_name = key.split('-')[0]
            return Artist.query.filter(Artist.site_filter('name', '__eq__', site_name),
                                       Artist.site_artist_id == value).one_or_none()
        if rel == 'posts':
            return Post.query.join(MediaAsset).filter(MediaAsset.md5.in_(k['md5'] for k in key)).all()

    @classproperty(cached=True)
    def load_columns(cls):
        return super().load_columns + ['site_name']

    archive_excludes = {'site', 'site_id'}
    archive_includes = {('site', 'site_name')}
    archive_scalars = ['commentaries', 'tags']
    archive_attachments = ['urls', ('data', 'site_data'), 'notations']
    archive_links = [('artist', 'site_artist_id'),
                     ('posts', 'active_urls', 'link_key', 'attach_post_by_link_key')]

    @classproperty(cached=True)
    def json_attributes(cls):
        return super().json_attributes + ['site_illust_id_str', 'urls', 'tags', 'commentaries', 'site_data']

    # ## Private

    @property
    def _urls_query(self):
        return IllustUrl.query.filter_by(illust_id=self.id)

    @property
    def _post_query(self):
        from .post import Post
        return Post.query.join(IllustUrl).filter(IllustUrl.illust_id == self.id)

    def _populate_posts(self):
        if len(self.urls) and any('post' in url._sa_instance_state.unloaded for url in self.urls):
            selectinload_batch_primary(self.urls, 'post')
        self._populate_posts = lambda: None

    __table_args__ = (
        DB.UniqueConstraint('site_illust_id', 'site_id'),
    )


# ## INITIALIZATION

def initialize():
    from .artist import Artist
    # Access the opposite side of the relationship to force the back reference to be generated
    Artist.illusts.property._configure_started
    Illust.set_relation_properties()
