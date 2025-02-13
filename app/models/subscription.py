# APP/MODELS/SUBSCRIPTION.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property

# ## PACKAGE IMPORTS
from utility.obj import classproperty, memoized_classproperty
from utility.data import inc_dict_entry, swap_list_values

# ## LOCAL IMPORTS
from .model_enums import SubscriptionStatus, SubscriptionElementStatus, SubscriptionElementKeep
from .illust import Illust
from .illust import IllustUrl
from .post import Post
from .notation import Notation
from .error import Error
from .subscription_element import SubscriptionElement
from .base import JsonModel, integer_column, real_column, enum_column, timestamp_column, register_enum_column,\
    relationship, backref


# ## FUNCTIONS

def populate_storage(func):
    def wrapper(*args):
        if not hasattr(args[0], '_total_bytes'):
            args[0]._populate_storage_sizes()
        return func(*args)
    return wrapper


def populate_keep(func):
    def wrapper(*args):
        if not hasattr(args[0], '_keep_counts'):
            args[0]._populate_keep_counts()
        return func(*args)
    return wrapper


def populate_status(func):
    def wrapper(*args):
        if not hasattr(args[0], '_status_counts'):
            args[0]._populate_status_counts()
        return func(*args)
    return wrapper


# ## CLASSES

class Subscription(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    artist_id = integer_column(foreign_key='artist.id', nullable=False, index=True)
    interval = real_column(nullable=False)
    expiration = real_column(nullable=True)
    status_id = enum_column(foreign_key='subscription_status.id', nullable=False)
    last_id = integer_column(nullable=True)
    requery = timestamp_column(nullable=True)
    checked = timestamp_column(nullable=True)
    created = timestamp_column(nullable=False)
    updated = timestamp_column(nullable=False)

    # ## Relationships
    elements = relationship(SubscriptionElement, uselist=True, cascade="all, delete",
                            backref=backref('subscription', uselist=False))
    errors = relationship(Error, uselist=True, cascade='all,delete',
                          backref=backref('subscription', uselist=False))
    notations = relationship(Notation, uselist=True, cascade='all,delete',
                             backref=backref('subscription', uselist=False))
    # (OtO) artist [Artist]

    # ## Instance properties

    @memoized_property
    def recent_posts(self):
        q = self._post_query
        q = q.order_by(Post.id.desc())
        page = q.count_paginate(per_page=10, distinct=True, count=False)
        return page.items

    @memoized_property
    def undecided_elements(self):
        return self._element_query.filter(SubscriptionElement.status_value == 'active',
                                          SubscriptionElement.keep_value.is_(None))\
                                  .all()

    @property
    @populate_storage
    def total_bytes(self):
        return self._total_bytes

    @property
    @populate_storage
    def main_bytes(self):
        return self._main_bytes

    @property
    @populate_storage
    def alternate_bytes(self):
        return self._alternate_bytes

    @memoized_property
    def element_count(self):
        return self._element_query.get_count()

    @memoized_property
    def illust_count(self):
        return self._illust_query.distinct_count()

    @memoized_property
    def post_count(self):
        return self._post_query.distinct_count()

    @memoized_property
    @populate_keep
    def undecided_count(self):
        return self._keep_counts.get('undecided', 0)

    @memoized_property
    @populate_keep
    def yes_count(self):
        return self._keep_counts.get('yes', 0)

    @memoized_property
    @populate_keep
    def no_count(self):
        return self._keep_counts.get('no', 0)

    @memoized_property
    @populate_keep
    def maybe_count(self):
        return self._keep_counts.get('maybe', 0)

    @memoized_property
    @populate_keep
    def archive_count(self):
        return self._keep_counts.get('undecided', 0)

    @memoized_property
    @populate_status
    def active_count(self):
        return self._status_counts.get('active', 0)

    @memoized_property
    @populate_status
    def unlinked_count(self):
        return self._status_counts.get('unlinked', 0)

    @memoized_property
    @populate_status
    def deleted_count(self):
        return self._status_counts.get('deleted', 0)

    @memoized_property
    @populate_status
    def archived_count(self):
        return self._status_counts.get('archived', 0)

    @memoized_property
    @populate_status
    def duplicate_count(self):
        return self._status_counts.get('deleted', 0)

    @memoized_property
    @populate_status
    def error_count(self):
        return self._status_counts.get('error', 0)

    @memoized_property
    def last_keep(self):
        return self._element_query.join(IllustUrl).join(Illust)\
                                  .filter(SubscriptionElement.keep_value == 'yes')\
                                  .order_by(Illust.site_created.desc())\
                                  .first()

    # ## Class properties

    @memoized_classproperty
    def repr_attributes(cls):
        mapping = {
            'status_id': ('status', 'status_name'),
        }
        return swap_list_values(super().repr_attributes, mapping)

    @classproperty
    def json_attributes(cls):
        return cls.repr_attributes

    # ## Private

    @property
    def _element_query(self):
        return SubscriptionElement.query.filter_by(subscription_id=self.id)

    @property
    def _illust_query(self):
        return Illust.query.join(IllustUrl).join(SubscriptionElement)\
                     .filter(SubscriptionElement.subscription_id == self.id)

    @property
    def _post_query(self):
        from .artist import Artist
        return Post.query.join(IllustUrl, Post.illust_urls)\
                         .join(Illust, IllustUrl.illust)\
                         .join(Artist, Illust.artist)\
                         .filter(Artist.id == self.artist_id, Post.type_value == 'subscription')

    def _populate_storage_sizes(self):
        if hasattr(self, '_total_bytes'):
            return
        if self.post_count == 0:
            self._total_bytes = self._main_bytes = self._alternate_bytes = 0
        else:
            filesizes = self._post_query.with_entities(Post.size, Post.alternate).all()
            self._total_bytes = sum([x[0] for x in filesizes])
            self._main_bytes = sum([x[0] for x in filesizes if x[1] is False])
            self._alternate_bytes = sum([x[0] for x in filesizes if x[1] is True])

    def _populate_keep_counts(self):
        keep_counts = self._element_query.with_entities(SubscriptionElement.keep_id).all()
        counts = {}
        for keep in keep_counts:
            keep_name = SubscriptionElementKeep.to_name(keep[0]) or 'undecided'
            inc_dict_entry(counts, keep_name)
        setattr(self, '_keep_counts', counts)

    def _populate_status_counts(self):
        if hasattr(self, '_status_counts'):
            return
        status_counts = self._element_query.with_entities(SubscriptionElement.status_id).all()
        counts = {}
        for status in status_counts:
            status_name = SubscriptionElementStatus.to_name(status[0])
            inc_dict_entry(counts, status_name)
        setattr(self, '_status_counts', counts)


# ## INITIALIZATION

def initialize():
    from .artist import Artist
    # Access the opposite side of the relationship to force the back reference to be generated
    Artist.subscription.property._configure_started
    Subscription.set_relation_properties()
    register_enum_column(Subscription, SubscriptionStatus, 'status')
