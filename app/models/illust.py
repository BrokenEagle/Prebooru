# APP/MODELS/ILLUST.PY

# ## EXTERNAL LINKS
from sqlalchemy.util import memoized_property
from sqlalchemy.orm import lazyload
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from utility.obj import classproperty
from utility.data import list_difference

# ## LOCAL IMPORTS
from .. import DB
from ..logical.sites import domain_by_site_name
from .model_enums import SiteDescriptor
from .tag import SiteTag, site_tag_creator
from .illust_url import IllustUrl
from .description import Description, description_creator
from .notation import Notation
from .pool_element import PoolIllust
from .base import JsonModel, integer_column, enum_column, boolean_column, timestamp_column, secondarytable,\
    register_enum_column, relationship, backref, relation_association_proxy


# ## GLOBAL VARIABLES

# Many-to-many tables

IllustTags = secondarytable('illust_tags',
                            ('illust_id', 'illust.id'),
                            ('tag_id', 'tag.id'))
IllustTitles = secondarytable('illust_titles',
                              ('illust_id', 'illust.id'),
                              ('description_id', 'description.id'))
IllustCommentaries = secondarytable('illust_commentaries',
                                    ('illust_id', 'illust.id'),
                                    ('description_id', 'description.id'))
AdditionalCommentaries = secondarytable('additional_commentaries',
                                        ('illust_id', 'illust.id'),
                                        ('description_id', 'description.id'))


# ## CLASSES

class Illust(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    site_id = enum_column(foreign_key='site_descriptor.id', nullable=False)
    site_illust_id = integer_column(nullable=False)
    site_created = timestamp_column(nullable=True)
    artist_id = integer_column(foreign_key='artist.id', nullable=False, index=True)
    title_id = integer_column(foreign_key='description.id', nullable=True)
    commentary_id = integer_column(foreign_key='description.id', nullable=True)
    pages = integer_column(nullable=False)
    score = integer_column(nullable=False)
    active = boolean_column(nullable=False)
    created = timestamp_column(nullable=False)
    updated = timestamp_column(nullable=False)

    # ## Relationships
    title = relationship(Description, uselist=False, foreign_keys=[title_id])
    commentary = relationship(Description, uselist=False, foreign_keys=[commentary_id])
    titles = relationship(Description, secondary=IllustTitles, uselist=True)
    commentaries = relationship(Description, secondary=IllustCommentaries, uselist=True)
    additional_commentaries = relationship(Description, secondary=AdditionalCommentaries, uselist=True)
    tags = relationship(SiteTag, secondary=IllustTags, uselist=True)
    urls = relationship(IllustUrl, uselist=True, cascade="all, delete", backref=backref('illust', uselist=False))
    notations = relationship(Notation, uselist=True, cascade='all,delete', backref=backref('illust', uselist=False))
    # Pool elements must be deleted individually, since pools will need to be reordered/recounted
    _pools = relationship(PoolIllust, uselist=True, backref=backref('item', uselist=False))
    # (OtO) artist [Artist]

    # ## Association proxies
    tag_names = association_proxy('tags', 'name', creator=site_tag_creator)
    title_body = relation_association_proxy('title_id', 'title', 'body', description_creator)
    commentary_body = relation_association_proxy('commentary_id', 'commentary', 'body', description_creator)
    pools = association_proxy('_pools', 'pool')
    boorus = association_proxy('artist', 'boorus')
    title_bodies = association_proxy('titles', 'body', creator=description_creator)
    commentary_bodies = association_proxy('commentaries', 'body', creator=description_creator)
    additional_commentary_bodies = association_proxy('additional_commentaries', 'body', creator=description_creator)

    # ## Instance properties

    @property
    def source(self):
        from ..logical.sources import source_by_site_name
        return source_by_site_name(self.site.name)

    @property
    def site_illust_id_str(self):
        return str(self.site_illust_id)

    @property
    def primary_url(self):
        return self.source.get_primary_url(self)

    @property
    def secondary_url(self):
        return self.source.get_secondary_url(self)

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

    @property
    def active_urls(self):
        return [url for url in self.urls if url.post_id is not None]

    @memoized_property
    def posts(self):
        return self._post_query.all()

    @property
    def post_count(self):
        return self._post_query.get_count()

    @property
    def titles_count(self):
        return IllustTitles.query.filter_by(illust_id=self.id).get_count()

    @property
    def commentaries_count(self):
        return IllustCommentaries.query.filter_by(illust_id=self.id).get_count()

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
        return domain_by_site_name(self.site_name)

    @property
    def sitelink(self):
        return "%s #%d" % (self.site.name.lower(), self.site_illust_id)

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
        site_illust_id = int(site_illust_id_str)
        return cls.query.filter(cls.site_value == site_name, cls.site_illust_id == site_illust_id).one_or_none()

    @classmethod
    def find_rel_by_key(cls, rel, key, value):
        from .artist import Artist
        from .post import Post
        if rel == 'artist':
            site_name = key.split('-')[0]
            return Artist.query.filter(Artist.site_value == site_name, Artist.site_artist_id == value).one_or_none()
        if rel == 'posts':
            return Post.query.filter(Post.md5.in_(k['md5'] for k in key)).all()

    @classproperty(cached=True)
    def load_columns(cls):
        return super().load_columns + ['site_name', 'title_body', 'commentary_body']

    archive_excludes = {'site', 'site_id', 'title_id', 'commentary_id'}
    archive_includes = {('site', 'site_name'), ('title', 'title_body'), ('commentary', 'commentary_body')}
    archive_scalars = [('tags', 'tag_names'), ('titles', 'title_bodies'),
                       ('commentaries', 'commentary_bodies'),
                       ('additional_commentaries', 'additional_commentary_bodies')]
    archive_attachments = ['urls', 'notations']
    archive_links = [('artist', 'site_artist_id'),
                     ('posts', 'active_urls', 'link_key', 'attach_post_by_link_key')]

    @classproperty(cached=True)
    def repr_attributes(cls):
        return list_difference(super().json_attributes, ['site_id', 'title_id', 'commentary_id']) + ['site_name']

    @classproperty(cached=True)
    def json_attributes(cls):
        return cls.repr_attributes + ['site_illust_id_str', 'title_body', 'commentary_body', 'tag_names', 'urls']

    # ## Private

    @property
    def _urls_query(self):
        return IllustUrl.query.filter_by(illust_id=self.id)

    @property
    def _post_query(self):
        from .post import Post
        return Post.query.join(IllustUrl, Post.illust_urls).filter(IllustUrl.illust_id == self.id)

    __table_args__ = (
        DB.UniqueConstraint('site_illust_id', 'site_id'),
    )


# ## INITIALIZATION

def initialize():
    from .artist import Artist
    # Access the opposite side of the relationship to force the back reference to be generated
    Artist.illusts.property._configure_started
    Illust.set_relation_properties()
    register_enum_column(Illust, SiteDescriptor, 'site')
