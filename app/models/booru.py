# APP/MODELS/BOORU.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from .artist import Artist
from .illust import Illust
from .illust_url import IllustUrl
from .post import Post
from .notation import Notation
from .label import Label
from .base import JsonModel, EpochTimestamp, secondarytable


# ## GLOBAL VARIABLES

BooruNames = secondarytable(
    'booru_names',
    DB.Column('label_id', DB.Integer, DB.ForeignKey('label.id'), primary_key=True),
    DB.Column('booru_id', DB.Integer, DB.ForeignKey('booru.id'), primary_key=True),
)

BooruArtists = secondarytable(
    'booru_artists',
    DB.Column('artist_id', DB.Integer, DB.ForeignKey('artist.id'), primary_key=True),
    DB.Column('booru_id', DB.Integer, DB.ForeignKey('booru.id'), primary_key=True),
)


# ## CLASSES

class Booru(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    danbooru_id = DB.Column(DB.Integer, unique=True, nullable=False)
    current_name = DB.Column(DB.String(255), nullable=False)
    banned = DB.Column(DB.Boolean, nullable=False)
    deleted = DB.Column(DB.Boolean, nullable=False)
    created = DB.Column(EpochTimestamp(nullable=False), nullable=False)
    updated = DB.Column(EpochTimestamp(nullable=False), nullable=False)

    # ## Relationships
    _names = DB.relationship(Label, secondary=BooruNames, lazy=True, uselist=True,
                             backref=DB.backref('boorus', lazy=True, uselist=True))
    artists = DB.relationship(Artist, secondary=BooruArtists, lazy=True, uselist=True,
                              backref=DB.backref('boorus', lazy=True))
    notations = DB.relationship(Notation, lazy=True, uselist=True, cascade='all,delete',
                                backref=DB.backref('booru', lazy=True, uselist=False))

    # ## Association proxies
    names = association_proxy('_names', 'name')
    artist_ids = association_proxy('artists', 'id')

    # ## Instance properties

    @memoized_property
    def recent_posts(self):
        q = self._post_query
        q = q.order_by(Post.id.desc())
        page = q.count_paginate(per_page=10, distinct=True, count=False)
        return page.items

    @memoized_property
    def illust_count(self):
        return self._illust_query.get_count()

    @memoized_property
    def post_count(self):
        return self._post_query.distinct_count()

    @memoized_property
    def _illust_query(self):
        return Illust.query.join(Artist, Illust.artist).join(Booru, Artist.boorus).filter(Booru.id == self.id)

    @memoized_property
    def _post_query(self):
        return Post.query.join(IllustUrl, Post.illust_urls).join(Illust, IllustUrl.illust).join(Artist, Illust.artist)\
                   .join(Booru, Artist.boorus).filter(Booru.id == self.id)

    def delete(self):
        self._names.clear()
        self.artists.clear()
        DB.session.delete(self)
        DB.session.commit()

    # ## Class properties

    @classproperty(cached=True)
    def json_attributes(cls):
        return super().json_attributes + ['names']
