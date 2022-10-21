# APP/MODELS/SUBSCRIPTION.PY

# ## PYTHON IMPORTS
import enum

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property

# ## PACKAGE IMPORTS
from utility.time import average_timedelta, days_ago, get_current_time

# ## LOCAL IMPORTS
from .. import DB
from .illust import Illust
from .illust import IllustUrl
from .post import Post
from .error import Error
from .subscription_element import SubscriptionElement
from .base import JsonModel, ModelEnum, IntEnum, EpochTimestamp, secondarytable


# ## GLOBAL VARIABLES

# Many-to-many tables

SubscriptionErrors = secondarytable(
    'subscription_errors',
    DB.Column('subscription_id', DB.Integer, DB.ForeignKey('subscription.id'), primary_key=True),
    DB.Column('error_id', DB.Integer, DB.ForeignKey('error.id'), primary_key=True),
    DB.Index(None, 'error_id', 'subscription_id'),
)


# ## CLASSES

class SubscriptionStatus(ModelEnum):
    idle = enum.auto()
    manual = enum.auto()
    automatic = enum.auto()
    error = enum.auto()


class Subscription(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    artist_id = DB.Column(DB.Integer, DB.ForeignKey('artist.id'), nullable=False, index=True)
    interval = DB.Column(DB.Float, nullable=False)
    expiration = DB.Column(DB.Float, nullable=True)
    status = DB.Column(IntEnum(SubscriptionStatus), nullable=False)
    last_id = DB.Column(DB.Integer, nullable=True)
    requery = DB.Column(EpochTimestamp(nullable=True), nullable=True)
    checked = DB.Column(EpochTimestamp(nullable=True), nullable=True)
    created = DB.Column(EpochTimestamp(nullable=False), nullable=False)
    updated = DB.Column(EpochTimestamp(nullable=False), nullable=False)
    active = DB.Column(DB.Boolean, nullable=False)

    # #### Relationships
    elements = DB.relationship(SubscriptionElement, lazy=True, cascade="all, delete",
                               backref=DB.backref('subscription', lazy=True, uselist=False))
    errors = DB.relationship(Error, secondary=SubscriptionErrors, lazy=True, cascade='all,delete',
                             backref=DB.backref('subscription', uselist=False, lazy=True))

    # ## Property methods

    @memoized_property
    def posts(self):
        q = self._post_query
        q = q.order_by(Post.id.desc())
        return q.all()

    @memoized_property
    def recent_posts(self):
        q = self._post_query
        q = q.distinct(Post.id)
        q = q.order_by(Post.id.desc())
        q = q.limit(10)
        return q.all()

    @memoized_property
    def active_elements(self):
        return self._element_query.filter_by(status='active').all()

    @memoized_property
    def average_interval(self):
        datetimes = self._illust_query.filter(Illust.site_created > days_ago(365),
                                              SubscriptionElement.keep == 'yes')\
                                      .order_by(Illust.site_illust_id.desc())\
                                      .with_entities(Illust.site_created)\
                                      .all()
        if len(datetimes) == 0:
            return
        datetimes = [get_current_time()] + [x[0] for x in datetimes]
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
        return self._illust_query.distinct().relation_count()

    @memoized_property
    def post_count(self):
        return self._post_query.distinct().relation_count()

    # ## Class properties
    status_enum = SubscriptionStatus

    # ## Private methods

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
                         .filter(Artist.id == self.artist_id, Post.type == Post.type_enum.subscription)

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


# ## INITIALIZATION

def initialize():
    from .artist import Artist
    # Access the opposite side of the relationship to force the back reference to be generated
    Artist.subscription.property._configure_started
    Subscription.set_relation_properties()
