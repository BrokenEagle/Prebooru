# APP/MODELS/SUBSCRIPTION_ELEMENT.PY

# ## LOCAL IMPORTS
from .. import DB
from ..enum_imports import subscription_element_status, subscription_element_keep
from .error import Error
from .base import JsonModel, BlobMD5, EpochTimestamp, secondarytable, get_relation_definitions


# ## GLOBAL VARIABLES

# Many-to-many tables

SubscriptionElementErrors = secondarytable(
    'subscription_element_errors',
    DB.Column('subscription_element_id', DB.Integer, DB.ForeignKey('subscription_element.id'),
              primary_key=True),
    DB.Column('error_id', DB.Integer, DB.ForeignKey('error.id'), primary_key=True),
    DB.Index(None, 'error_id', 'subscription_element_id'),
)


# ## CLASSES

class SubscriptionElement(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    subscription_id = DB.Column(DB.Integer, DB.ForeignKey('subscription.id'), nullable=False, index=True)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=True)
    illust_url_id = DB.Column(DB.Integer, DB.ForeignKey('illust_url.id'), nullable=False)
    md5 = DB.Column(BlobMD5(nullable=True), nullable=True)
    keep, keep_id, keep_enum, keep_filter, keep_col =\
        get_relation_definitions(subscription_element_keep, relname='keep', relcol='id', colname='keep_id',
                                 tblname='subscription_element', nullable=True)
    expires = DB.Column(EpochTimestamp(nullable=True), nullable=True)
    status, status_id, status_enum, status_filter, status_col =\
        get_relation_definitions(subscription_element_status, relname='status', relcol='id', colname='status_id',
                                 tblname='subscription_element', nullable=False)

    # ## Relationships
    errors = DB.relationship(Error, secondary=SubscriptionElementErrors, lazy=True, uselist=True, cascade='all,delete',
                             backref=DB.backref('subscription_element', lazy=True, uselist=False))
    # (MtO) subscription [Susbscription]
    # (MtO) post [Post]
    # (OtO) illust_url [IllustUrl]

    # ## Instance properties

    @property
    def duplicate_elements(self):
        return self._duplicate_element_query.all()

    @property
    def duplicate_element_count(self):
        return self._duplicate_element_query.get_count()

    # ## Class properties

    # ## Private

    @property
    def _duplicate_element_query(self):
        return SubscriptionElement.query.filter(SubscriptionElement.md5 == self.md5, SubscriptionElement.id != self.id)


# ## INITIALIZATION

def initialize():
    from .subscription import Subscription
    DB.Index(None, SubscriptionElement.md5, unique=False, sqlite_where=SubscriptionElement.md5.is_not(None))
    DB.Index(None, SubscriptionElement.post_id, unique=True, sqlite_where=SubscriptionElement.post_id.is_not(None))
    # Access the opposite side of the relationship to force the back reference to be generated
    Subscription.elements.property._configure_started
    SubscriptionElement.set_relation_properties()
