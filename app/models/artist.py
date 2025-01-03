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
from .label import Label, label_creator
from .description import Description, description_creator
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


# ## CLASSES

class Artist(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    site, site_id, site_name, site_enum, site_filter, site_col =\
        get_relation_definitions(site_descriptor, relname='site', relcol='id', colname='site_id',
                                 tblname='artist', nullable=False)
    site_artist_id = DB.Column(DB.Integer, nullable=False)
    current_site_account = DB.Column(DB.String(255), nullable=False)
    site_created = DB.Column(EpochTimestamp(nullable=True), nullable=True)
    active = DB.Column(DB.Boolean, nullable=False)
    primary = DB.Column(DB.Boolean, nullable=False)
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
    notations = DB.relationship(Notation, lazy=True, uselist=True, cascade='all,delete',
                                backref=DB.backref('artist', lazy=True, uselist=False))
    # (MtM) boorus [Booru]

    # ## Association proxies
    site_accounts = association_proxy('_site_accounts', 'name', creator=label_creator)
    names = association_proxy('_names', 'name', creator=label_creator)
    profiles = association_proxy('_profiles', 'body', creator=description_creator)

    # ## Instance properties

    @property
    def source(self):
        return self.site.source

    @property
    def site_artist_id_str(self):
        return str(self.site_artist_id)

    @property
    def primary_url(self):
        return self.source.ARTIST_HREFURL % self.site_artist_id

    @property
    def other_site_accounts(self):
        return [account for account in self.site_accounts if account != self.current_site_account]

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

    @memoized_property
    def last_illust(self):
        return self._illust_query.order_by(Illust.site_illust_id.desc()).first()

    @memoized_property
    def first_illust(self):
        return self._illust_query.order_by(Illust.site_illust_id.asc()).first()

    @property
    def last_illust_id(self):
        return self.last_illust.site_illust_id if self.last_illust is not None else None

    @property
    def first_illust_id(self):
        return self.first_illust.site_illust_id if self.first_illust is not None else None

    @property
    def sitelink(self):
        return self.source.ARTIST_SHORTLINK % self.site_artist_id

    @property
    def site_domain(self):
        return self.site.domain

    @property
    def booru_search_url(self):
        return self.source.artist_booru_search_url(self)

    @property
    def key(self):
        return '%s-%d' % (self.site.name, self.site_artist_id)

    def delete(self):
        self._names.clear()
        self._profiles.clear()
        self._site_accounts.clear()
        DB.session.delete(self)
        DB.session.commit()

    # ## Class properties

    @classmethod
    def find_by_key(cls, key):
        site_name, site_artist_id_str = key.split('-')
        enum_filter = cls.site_filter('name', '__eq__', site_name)
        id_filter = cls.site_artist_id == int(site_artist_id_str)
        return cls.query.enum_join(cls.site_enum)\
                        .filter(enum_filter, id_filter)\
                        .one_or_none()

    @classproperty(cached=True)
    def load_columns(cls):
        return super().load_columns + ['site_name']

    archive_excludes = {'site', 'site_id', 'current_site_account'}
    archive_includes = {('site', 'site_name'), ('current_account', 'current_site_account')}
    archive_scalars = ['profiles', 'names', ('accounts', 'other_site_accounts', 'site_accounts',
                                             lambda x: x.site_accounts.append(x.current_site_account))]
    archive_attachments = ['webpages', 'notations']
    archive_links = [('boorus', 'danbooru_id')]

    @classproperty(cached=True)
    def json_attributes(cls):
        return super().json_attributes + ['site_artist_id_str', 'site_accounts', 'names', 'webpages', 'profiles']

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
