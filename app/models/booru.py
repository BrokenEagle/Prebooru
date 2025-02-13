# APP/MODELS/BOORU.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from utility.obj import classproperty, memoized_classproperty
from utility.data import swap_list_values

# ## LOCAL IMPORTS
from .. import DB
from .artist import Artist
from .illust import Illust
from .illust_url import IllustUrl
from .post import Post
from .notation import Notation
from .label import Label, label_creator
from .base import JsonModel, integer_column, boolean_column, timestamp_column, secondarytable, relationship, backref,\
    relation_association_proxy


# ## GLOBAL VARIABLES

BooruNames = secondarytable('booru_names', ('booru_id', 'booru.id'), ('label_id', 'label.id'))
BooruArtists = secondarytable('booru_artists', ('booru_id', 'booru.id'), ('artist_id', 'artist.id'), index=True)


# ## CLASSES

class Booru(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    danbooru_id = integer_column(nullable=True)
    name_id = integer_column(foreign_key='label.id', nullable=False)
    banned = boolean_column(nullable=False)
    deleted = boolean_column(nullable=False)
    created = timestamp_column(nullable=False)
    updated = timestamp_column(nullable=False)

    # ## Relationships
    name = relationship(Label, uselist=False)
    names = relationship(Label, secondary=BooruNames, uselist=True, backref=backref('boorus', uselist=True))
    artists = relationship(Artist, secondary=BooruArtists, uselist=True, backref=backref('boorus', uselist=True))
    notations = relationship(Notation, uselist=True, cascade='all,delete', backref=backref('booru', uselist=False))

    # ## Association proxies
    name_value = relation_association_proxy('name_id', 'name', 'name', label_creator)
    name_values = association_proxy('names', 'name', creator=label_creator)
    artist_ids = association_proxy('artists', 'id')

    # ## Instance properties

    @memoized_property
    def recent_posts(self):
        q = self._post_query
        q = q.order_by(Post.id.desc())
        page = q.count_paginate(per_page=10, distinct=True, count=False)
        return page.items

    @property
    def illust_count(self):
        return self._illust_query.get_count()

    @property
    def post_count(self):
        return self._post_query.distinct_count()

    @property
    def names_count(self):
        return BooruNames.query.filter_by(booru_id=self.id).get_count()

    # ## Class properties

    @memoized_classproperty
    def repr_attributes(cls):
        mapping = {
            'name_id': ('name', 'name_value'),
        }
        return swap_list_values(super().repr_attributes, mapping)

    @classproperty
    def json_attributes(cls):
        return cls.repr_attributes

    # ## Private
    @property
    def _illust_query(self):
        return Illust.query.join(Artist, Illust.artist).join(Booru, Artist.boorus).filter(Booru.id == self.id)

    @property
    def _post_query(self):
        return Post.query.join(IllustUrl, Post.illust_urls).join(Illust, IllustUrl.illust).join(Artist, Illust.artist)\
                   .join(Booru, Artist.boorus).filter(Booru.id == self.id)


# ## INITIALIZATION

def initialize():
    DB.Index(None, Booru.danbooru_id, unique=True, sqlite_where=Booru.danbooru_id.is_not(None))
