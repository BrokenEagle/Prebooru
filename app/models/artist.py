# APP/MODELS/ARTIST.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from utility.obj import classproperty
from utility.data import list_difference

# ## LOCAL IMPORTS
from .. import DB
from ..logical.sites import domain_by_site_name
from .model_enums import SiteDescriptor
from .artist_url import ArtistUrl
from .illust import Illust
from .label import Label, label_creator
from .description import Description, description_creator
from .subscription import Subscription
from .post import Post
from .illust_url import IllustUrl
from .notation import Notation
from .base import JsonModel, integer_column, enum_column, boolean_column, timestamp_column, secondarytable,\
    register_enum_column, relationship, backref, relation_association_proxy


# ## GLOBAL VARIABLES

ArtistNames = secondarytable('artist_names', ('artist_id', 'artist.id'), ('label_id', 'label.id'))
ArtistSiteAccounts = secondarytable('artist_site_accounts', ('artist_id', 'artist.id'), ('label_id', 'label.id'))
ArtistProfiles = secondarytable('artist_profiles', ('artist_id', 'artist.id'), ('description_id', 'description.id'))


# ## CLASSES

class Artist(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    site_id = enum_column(foreign_key='site_descriptor.id', nullable=False)
    site_artist_id = integer_column(nullable=False)
    site_account_id = integer_column(foreign_key='label.id', nullable=False)
    name_id = integer_column(foreign_key='label.id', nullable=True)
    profile_id = integer_column(foreign_key='description.id', nullable=True)
    site_created = timestamp_column(nullable=True)
    active = boolean_column(nullable=False)
    primary = boolean_column(nullable=False)
    created = timestamp_column(nullable=False)
    updated = timestamp_column(nullable=False)

    # ## Relationships
    site_account = relationship(Label, uselist=False, foreign_keys=[site_account_id])
    name = relationship(Label, uselist=False, foreign_keys=[name_id])
    profile = relationship(Description, uselist=False)
    site_accounts = relationship(Label, secondary=ArtistSiteAccounts, uselist=True)
    names = relationship(Label, secondary=ArtistNames, uselist=True)
    profiles = relationship(Description, secondary=ArtistProfiles, uselist=True)
    illusts = relationship(Illust, uselist=True, cascade="all, delete", backref=backref('artist', uselist=False))
    subscription = relationship(Subscription, uselist=False, cascade="all, delete",
                                backref=backref('artist', uselist=False))
    webpages = relationship(ArtistUrl, uselist=True, cascade="all, delete", backref=backref('artist', uselist=False))
    notations = relationship(Notation, uselist=True, cascade='all,delete', backref=backref('artist', uselist=False))
    # (MtM) boorus [Booru]

    # ## Association proxies
    site_account_value = relation_association_proxy('site_account_id', 'site_account', 'name', label_creator)
    name_value = relation_association_proxy('name_id', 'name', 'name', label_creator)
    profile_body = relation_association_proxy('profile_id', 'profile', 'body', description_creator)
    site_account_values = association_proxy('site_accounts', 'name', creator=label_creator)
    name_values = association_proxy('names', 'name', creator=label_creator)
    profile_bodies = association_proxy('profiles', 'body', creator=description_creator)

    # ## Instance properties

    @property
    def source(self):
        from ..logical.sources import source_by_site_name
        return source_by_site_name(self.site.name)

    @property
    def site_artist_id_str(self):
        return str(self.site_artist_id)

    @property
    def primary_url(self):
        return self.source.ARTIST_HREFURL % self.site_artist_id

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
    def site_accounts_count(self):
        return ArtistSiteAccounts.query.filter_by(artist_id=self.id).get_count()

    @property
    def names_count(self):
        return ArtistNames.query.filter_by(artist_id=self.id).get_count()

    @property
    def profiles_count(self):
        return ArtistProfiles.query.filter_by(artist_id=self.id).get_count()

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
        return domain_by_site_name(self.site_name)

    @property
    def booru_search_url(self):
        return self.source.artist_booru_search_url(self)

    def delete(self):
        self.names.clear()
        self.profiles.clear()
        self.site_accounts.clear()
        DB.session.delete(self)
        DB.session.commit()

    # ## Class properties

    @classproperty(cached=True)
    def repr_attributes(cls):
        return list_difference(super().json_attributes, ['site_id', 'site_account_id', 'name_id', 'profile_id'])\
            + ['site_name', 'site_account_value', 'name_value']

    @classproperty(cached=True)
    def json_attributes(cls):
        return cls.repr_attributes + ['site_artist_id_str', 'profile_body', 'webpages']

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


# ## Initialize

def initialize():
    register_enum_column(Artist, SiteDescriptor, 'site')
