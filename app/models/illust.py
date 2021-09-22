# APP/MODELS/ILLUST.PY

# ##PYTHON IMPORTS
import datetime
from typing import List
from dataclasses import dataclass
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

# ##LOCAL IMPORTS
from .. import DB
from ..logical.sites import get_site_domain, get_site_key
from .base import JsonModel, date_time_or_null, remove_keys, int_or_none, polymorphic_accessor_factory
from .tag import Tag
from .illust_url import IllustUrl
from .site_data import SiteData
from .description import Description
from .notation import Notation
from .pool_element import PoolIllust


# ##GLOBAL VARIABLES

# Many-to-many tables

IllustTags = DB.Table(
    'illust_tags',
    DB.Column('tag_id', DB.Integer, DB.ForeignKey('tag.id'), primary_key=True),
    DB.Column('illust_id', DB.Integer, DB.ForeignKey('illust.id'), primary_key=True),
)

IllustCommentaries = DB.Table(
    'illust_commentaries',
    DB.Column('description_id', DB.Integer, DB.ForeignKey('description.id'), primary_key=True),
    DB.Column('illust_id', DB.Integer, DB.ForeignKey('illust.id'), primary_key=True),
)

IllustNotations = DB.Table(
    'illust_notations',
    DB.Column('illust_id', DB.Integer, DB.ForeignKey('illust.id'), primary_key=True),
    DB.Column('notation_id', DB.Integer, DB.ForeignKey('notation.id'), primary_key=True),
)


# CLASSES

@dataclass
class Illust(JsonModel):
    # ## Declarations

    # #### JSON format
    id: int
    site_id: int
    site_illust_id: int
    site_created: date_time_or_null
    commentaries: List[lambda x: x['body']]
    tags: List[lambda x: x['name']]
    urls: List[lambda x: remove_keys(x, ['id', 'illust_id'])]
    artist_id: int
    pages: int
    score: int_or_none
    site_data: lambda x: remove_keys(x.to_json(), ['id', 'illust_id', 'type'])
    active: bool
    requery: date_time_or_null
    created: datetime.datetime.isoformat
    updated: datetime.datetime.isoformat

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    site_id = DB.Column(DB.Integer, nullable=False)
    site_illust_id = DB.Column(DB.Integer, nullable=False)
    site_created = DB.Column(DB.DateTime(timezone=False), nullable=True)
    artist_id = DB.Column(DB.Integer, DB.ForeignKey('artist.id'), nullable=False)
    pages = DB.Column(DB.Integer, nullable=True)
    score = DB.Column(DB.Integer, nullable=True)
    active = DB.Column(DB.Boolean, nullable=True)
    requery = DB.Column(DB.DateTime(timezone=False), nullable=True)
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)
    updated = DB.Column(DB.DateTime(timezone=False), nullable=False)

    # #### Relationships
    commentaries = DB.relationship(Description, secondary=IllustCommentaries, lazy=True, backref=DB.backref('illusts', lazy=True))
    tags = DB.relationship(Tag, secondary=IllustTags, lazy=True, backref=DB.backref('illusts', lazy=True))
    urls = DB.relationship(IllustUrl, backref=DB.backref('illust', lazy=True, uselist=False), lazy=True, cascade="all, delete")
    site_data = DB.relationship(SiteData, lazy=True, uselist=False, cascade="all, delete")
    notations = DB.relationship(Notation, secondary=IllustNotations, lazy=True, backref=DB.backref('illust', uselist=False, lazy=True), cascade='all,delete')
    _pools = DB.relationship(PoolIllust, lazy=True, backref=DB.backref('item', lazy=True, uselist=False), cascade='all,delete')
    # artist <- Artist (OtO)

    # #### Association proxies
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

    # ## Property methods

    @memoized_property
    def ordered_urls(self):
        return sorted(self.urls, key=lambda x: x.order)

    @memoized_property
    def posts(self):
        return [post for post in self._posts if post is not None]

    @property
    def site_domain(self):
        return get_site_domain(self.site_id)

    @memoized_property
    def type(self):
        if self._source.illust_has_videos(self):
            return 'video'
        elif self._source.illust_has_images(self):
            return 'image'
        else:
            return 'unknown'

    @memoized_property
    def video_illust_url(self):
        return self._source.video_illust_video_url(self) if self.type == 'video' else None

    @memoized_property
    def thumb_illust_url(self):
        return self._source.video_illust_thumb_url(self) if self.type == 'video' else None

    # ###### Private

    @memoized_property
    def _source(self):
        from ..sources import SOURCEDICT
        site_key = get_site_key(self.site_id)
        return SOURCEDICT[site_key]

    # ## methods

    def delete(self):
        pools = [pool for pool in self.pools]
        DB.session.delete(self)
        DB.session.commit()
        if len(pools) > 0:
            for pool in pools:
                pool._elements.reorder()
            DB.session.commit()

    # ## Class properties

    basic_attributes = ['id', 'site_id', 'site_illust_id', 'site_created', 'artist_id', 'pages', 'score', 'active', 'created', 'updated', 'requery']
    relation_attributes = ['artist', 'urls', 'tags', 'commentaries', 'notations']
    searchable_attributes = basic_attributes + relation_attributes
