# APP/MODELS/SUBSCRIPTION.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property

# ## PACKAGE IMPORTS
from utility.time import average_timedelta, days_ago, get_current_time

# ## LOCAL IMPORTS
from .. import DB
from ..enum_imports import subscription_status, subscription_element_status, subscription_element_keep
from .illust import Illust
from .illust import IllustUrl
from .post import Post
from .notation import Notation
from .error import Error
from .subscription_element import SubscriptionElement
from .base import JsonModel, EpochTimestamp, get_relation_definitions


# ## CLASSES

class Subscription(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    artist_id = DB.Column(DB.Integer, DB.ForeignKey('artist.id'), nullable=False, index=True)
    interval = DB.Column(DB.Float, nullable=False)
    expiration = DB.Column(DB.Float, nullable=True)
    status, status_id, status_name, status_enum, status_filter, status_col =\
        get_relation_definitions(subscription_status, relname='status', relcol='id', colname='status_id',
                                 tblname='subscription', nullable=False)
    last_id = DB.Column(DB.Integer, nullable=True)
    requery = DB.Column(EpochTimestamp(nullable=True), nullable=True)
    checked = DB.Column(EpochTimestamp(nullable=True), nullable=True)
    created = DB.Column(EpochTimestamp(nullable=False), nullable=False)
    updated = DB.Column(EpochTimestamp(nullable=False), nullable=False)

    # ## Relationships
    elements = DB.relationship(SubscriptionElement, lazy=True, uselist=True, cascade="all, delete",
                               backref=DB.backref('subscription', lazy=True, uselist=False))
    errors = DB.relationship(Error, lazy=True, uselist=True, cascade='all,delete',
                             backref=DB.backref('subscription', uselist=False, lazy=True))
    notations = DB.relationship(Notation, lazy=True, uselist=True, cascade='all,delete',
                                backref=DB.backref('subscription', lazy=True, uselist=False))
    # (OtO) artist [Artist]

    # ## Instance properties

    @memoized_property
    def posts(self):
        q = self._post_query
        q = q.order_by(Post.id.desc())
        return q.all()

    @memoized_property
    def recent_posts(self):
        q = self._post_query
        q = q.order_by(Post.id.desc())
        page = q.count_paginate(per_page=10, distinct=True, count=False)
        return page.items

    @memoized_property
    def undecided_elements(self):
        return self._element_query.filter(SubscriptionElement.status_filter('name', '__eq__', 'active'),
                                          SubscriptionElement.keep_filter('name', 'is_', None)).all()

    @memoized_property
    def average_interval(self):
        datetimes = self._illust_query.filter(Illust.site_created > days_ago(365),
                                              SubscriptionElement.keep_filter('name', '__eq__', 'yes'))\
                                      .order_by(Illust.site_illust_id.desc())\
                                      .with_entities(Illust.site_created)\
                                      .all()
        if len(datetimes) == 0:
            return
        datetimes = [x[0] for x in datetimes]
        if self.undecided_count == 0:
            datetimes = [get_current_time()] + datetimes
        timedeltas = [datetimes[i - 1] - datetimes[i] for i in range(1, len(datetimes))]
        return average_timedelta(timedeltas)

    @property
    def total_bytes(self):
        self._populate_storage_sizes()
        return self._total_bytes

    @property
    def main_bytes(self):
        self._populate_storage_sizes()
        return self._main_bytes

    @property
    def alternate_bytes(self):
        self._populate_storage_sizes()
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
    def undecided_count(self):
        self._populate_keep_counts()
        return self._keep_counts['undecided']

    @memoized_property
    def yes_count(self):
        self._populate_keep_counts()
        return self._keep_counts['yes']

    @memoized_property
    def no_count(self):
        self._populate_keep_counts()
        return self._keep_counts['no']

    @memoized_property
    def maybe_count(self):
        self._populate_keep_counts()
        return self._keep_counts['maybe']

    @memoized_property
    def archive_count(self):
        self._populate_keep_counts()
        return self._keep_counts['archive']

    @memoized_property
    def active_count(self):
        self._populate_status_counts()
        return self._status_counts['active']

    @memoized_property
    def unlinked_count(self):
        self._populate_status_counts()
        return self._status_counts['unlinked']

    @memoized_property
    def deleted_count(self):
        self._populate_status_counts()
        return self._status_counts['deleted']

    @memoized_property
    def archived_count(self):
        self._populate_status_counts()
        return self._status_counts['archived']

    @memoized_property
    def duplicate_count(self):
        self._populate_status_counts()
        return self._status_counts['duplicate']

    @memoized_property
    def error_count(self):
        self._populate_status_counts()
        return self._status_counts['error']

    @memoized_property
    def last_keep(self):
        return self._element_query.enum_join(SubscriptionElement.keep_enum).join(IllustUrl).join(Illust)\
                                  .filter(SubscriptionElement.keep_filter('name', '__eq__', 'yes'))\
                                  .order_by(Illust.site_created.desc()).first()

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
                         .filter(Artist.id == self.artist_id, Post.type_filter('name', '__eq__', 'subscription'))

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
        if hasattr(self, '_keep_counts'):
            return
        keep_counts = self._element_query.with_entities(SubscriptionElement.keep_col()).all()
        counts = {name: 0 for name in subscription_element_keep.names + ['undecided']}
        for keep in keep_counts:
            keep_enum = _get_enum_id(keep[0])
            keep_value = subscription_element_keep.by_id(keep_enum) if keep_enum is not None else None
            keep_name = keep_value.name if keep_value is not None else 'undecided'
            counts[keep_name] = 1 + (counts[keep_name] if keep_name in counts else 0)
        setattr(self, '_keep_counts', counts)

    def _populate_status_counts(self):
        if hasattr(self, '_status_counts'):
            return
        status_counts = self._element_query.with_entities(SubscriptionElement.status_col()).all()
        counts = {name: 0 for name in subscription_element_status.names}
        for status in status_counts:
            status_enum = _get_enum_id(status[0])
            status_value = subscription_element_status.by_id(status_enum)
            status_name = status_value.name
            counts[status_name] = 1 + (counts[status_name] if status_name in counts else 0)
        setattr(self, '_status_counts', counts)


# ## INITIALIZATION

def initialize():
    from .artist import Artist
    # Access the opposite side of the relationship to force the back reference to be generated
    Artist.subscription.property._configure_started
    Subscription.set_relation_properties()


# ## Private

def _get_enum_id(value):
    return value if isinstance(value, int) or value is None else value.id
