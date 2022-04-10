# APP/MODELS/ARTIST.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

# ## LOCAL IMPORTS
from .. import DB
from ..logical.sites import get_site_domain, get_site_key
from .artist_url import ArtistUrl
from .illust import Illust
from .label import Label
from .description import Description
from .subscription_pool import SubscriptionPool
from .post import Post
from .illust_url import IllustUrl
from .notation import Notation
from .base import JsonModel


# ## GLOBAL VARIABLES

ArtistNames = DB.Table(
    'artist_names',
    DB.Column('label_id', DB.Integer, DB.ForeignKey('label.id'), primary_key=True),
    DB.Column('artist_id', DB.Integer, DB.ForeignKey('artist.id'), primary_key=True),
)

ArtistSiteAccounts = DB.Table(
    'artist_site_accounts',
    DB.Column('label_id', DB.Integer, DB.ForeignKey('label.id'), primary_key=True),
    DB.Column('artist_id', DB.Integer, DB.ForeignKey('artist.id'), primary_key=True),
)

ArtistProfiles = DB.Table(
    'artist_profiles',
    DB.Column('description_id', DB.Integer, DB.ForeignKey('description.id'), primary_key=True),
    DB.Column('artist_id', DB.Integer, DB.ForeignKey('artist.id'), primary_key=True),
)

ArtistNotations = DB.Table(
    'artist_notations',
    DB.Column('notation_id', DB.Integer, DB.ForeignKey('notation.id'), primary_key=True),
    DB.Column('artist_id', DB.Integer, DB.ForeignKey('artist.id'), primary_key=True),
)


# ## CLASSES

class Artist(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    site_id = DB.Column(DB.Integer, nullable=False)
    site_artist_id = DB.Column(DB.Integer, nullable=True)
    current_site_account = DB.Column(DB.String(255), nullable=True)
    site_created = DB.Column(DB.DateTime(timezone=False), nullable=True)
    active = DB.Column(DB.Boolean, nullable=True)
    requery = DB.Column(DB.DateTime(timezone=False), nullable=True)
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)
    updated = DB.Column(DB.DateTime(timezone=False), nullable=False)

    # #### Relationships
    _site_accounts = DB.relationship(Label, secondary=ArtistSiteAccounts, lazy=True)
    _names = DB.relationship(Label, secondary=ArtistNames, lazy=True)
    _profiles = DB.relationship(Description, secondary=ArtistProfiles, lazy=True)
    illusts = DB.relationship(Illust, lazy=True, backref=DB.backref('artist', lazy=True), cascade="all, delete")
    subscription_pool = DB.relationship(SubscriptionPool, lazy=True, uselist=False, backref=DB.backref('artist', uselist=False, lazy=True), cascade="all, delete")
    webpages = DB.relationship(ArtistUrl, backref='artist', lazy=True, cascade="all, delete")
    notations = DB.relationship(Notation, secondary=ArtistNotations, lazy=True,
                                backref=DB.backref('artist', uselist=False, lazy=True))
    # boorus <- Booru (MtM)

    # #### Association proxies
    site_accounts = association_proxy('_site_accounts', 'name')
    names = association_proxy('_names', 'name')
    profiles = association_proxy('_profiles', 'body')

    # ## Property methods

    @memoized_property
    def recent_posts(self):
        q = self._post_query
        q = q.order_by(Post.id.desc())
        q = q.limit(10)
        return q.all()

    @property
    def booru_count(self):
        return self._booru_query.get_count()

    @property
    def illust_count(self):
        return self._illust_query.get_count()

    @property
    def post_count(self):
        return self._post_query.get_count()

    @property
    def site_domain(self):
        return get_site_domain(self.site_id)

    @property
    def booru_search_url(self):
        return self._source.artist_booru_search_url(self)

    # ###### Private

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

    @memoized_property
    def _source(self):
        from ..logical.sources import SOURCEDICT
        site_key = get_site_key(self.site_id)
        return SOURCEDICT[site_key]

    # ## Methods

    def delete(self):
        self._names.clear()
        self._profiles.clear()
        self._site_accounts.clear()
        DB.session.delete(self)
        DB.session.commit()

    # ## Class properties

    basic_attributes = ['id', 'site_id', 'site_artist_id', 'site_created', 'current_site_account', 'active',
                        'created', 'updated', 'requery']
    relation_attributes = ['names', 'site_accounts', 'profiles', 'webpages', 'illusts', 'boorus', 'subscription_pool']
    searchable_attributes = basic_attributes + relation_attributes
    json_attributes = basic_attributes + ['site_accounts', 'names', 'webpages', 'profiles']
