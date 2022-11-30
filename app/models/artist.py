# APP/MODELS/ARTIST.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..enum_imports import site_descriptor
from .artist_url import ArtistUrl
from .illust import Illust
from .label import Label
from .description import Description
from .subscription import Subscription
from .post import Post
from .illust_url import IllustUrl
from .notation import Notation
from .base import JsonModel, EpochTimestamp, secondarytable, get_relation_definitions


# ## GLOBAL VARIABLES

ArtistNames = secondarytable(
    'artist_names',
    DB.Column('artist_id', DB.Integer, DB.ForeignKey('artist.id'), primary_key=True),
    DB.Column('label_id', DB.Integer, DB.ForeignKey('label.id'), primary_key=True),
)

ArtistSiteAccounts = secondarytable(
    'artist_site_accounts',
    DB.Column('artist_id', DB.Integer, DB.ForeignKey('artist.id'), primary_key=True),
    DB.Column('label_id', DB.Integer, DB.ForeignKey('label.id'), primary_key=True),
)

ArtistProfiles = secondarytable(
    'artist_profiles',
    DB.Column('artist_id', DB.Integer, DB.ForeignKey('artist.id'), primary_key=True),
    DB.Column('description_id', DB.Integer, DB.ForeignKey('description.id'), primary_key=True),
)

ArtistNotations = secondarytable(
    'artist_notations',
    DB.Column('artist_id', DB.Integer, DB.ForeignKey('artist.id'), primary_key=True),
    DB.Column('notation_id', DB.Integer, DB.ForeignKey('notation.id'), primary_key=True),
    DB.Index(None, 'notation_id', 'artist_id'),
)


# ## CLASSES

class Artist(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    site, site_id, site_enum, site_filter =\
        get_relation_definitions(site_descriptor, relname='site', relcol='id', colname='site_id',
                                 tblname='artist', nullable=False)
    site_artist_id = DB.Column(DB.Integer, nullable=False)
    current_site_account = DB.Column(DB.String(255), nullable=False)
    site_created = DB.Column(EpochTimestamp(nullable=True), nullable=True)
    active = DB.Column(DB.Boolean, nullable=False)
    created = DB.Column(EpochTimestamp(nullable=False), nullable=False)
    updated = DB.Column(EpochTimestamp(nullable=False), nullable=False)

    # ## Relationships
    _site_accounts = DB.relationship(Label, secondary=ArtistSiteAccounts, lazy=True, uselist=True,
                                     backref=DB.backref('site_account_artists', lazy=True, uselist=True))
    _names = DB.relationship(Label, secondary=ArtistNames, lazy=True, uselist=True,
                             backref=DB.backref('name_artists', lazy=True, uselist=True))
    _profiles = DB.relationship(Description, secondary=ArtistProfiles, lazy=True, uselist=True,
                                backref=DB.backref('artists', lazy=True, uselist=True))
    illusts = DB.relationship(Illust, lazy=True, uselist=True, cascade="all, delete",
                              backref=DB.backref('artist', lazy=True, uselist=False))
    subscription = DB.relationship(Subscription, lazy=True, uselist=False, cascade="all, delete",
                                   backref=DB.backref('artist', lazy=True, uselist=False))
    webpages = DB.relationship(ArtistUrl, lazy=True, uselist=True, cascade="all, delete",
                               backref=DB.backref('artist', lazy=True, uselist=False))
    notations = DB.relationship(Notation, secondary=ArtistNotations, lazy=True,
                                backref=DB.backref('artist', lazy=True, uselist=False))
    # (MtM) boorus [Booru]

    # ## Association proxies
    site_accounts = association_proxy('_site_accounts', 'name')
    names = association_proxy('_names', 'name')
    profiles = association_proxy('_profiles', 'body')

    # ## Instance properties

    @memoized_property
    def recent_posts(self):
        q = self._post_query
        q = q.order_by(Post.id.desc())
        page = q.count_paginate(per_page=10, distinct=True, count=False)
        return page.items

    @property
    def booru_count(self):
        return self._booru_query.get_count()

    @property
    def illust_count(self):
        return self._illust_query.get_count()

    @property
    def post_count(self):
        return self._post_query.distinct_count()

    @property
    def site_domain(self):
        return self.site.domain

    @property
    def booru_search_url(self):
        return self.site.source.artist_booru_search_url(self)

    def delete(self):
        self._names.clear()
        self._profiles.clear()
        self._site_accounts.clear()
        DB.session.delete(self)
        DB.session.commit()

    # ## Class properties

    @classproperty(cached=True)
    def json_attributes(cls):
        return super().json_attributes + ['site_accounts', 'names', 'webpages', 'profiles']

    # ## Private

    @property
    def _booru_query(self):
        from .booru import Booru
        return Booru.query.join(Artist, Booru.artists).filter(Artist.id == self.id)

    @property
    def _illust_query(self):
        return Illust.query.filter_by(artist_id=self.id)

    @property
    def _post_query(self):
        return Post.query.join(IllustUrl, Post.illust_urls).join(Illust, IllustUrl.illust)\
                   .filter(Illust.artist_id == self.id)

    __table_args__ = (
        DB.UniqueConstraint('site_artist_id', 'site_id'),
    )
