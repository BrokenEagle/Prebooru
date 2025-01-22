# APP/MODELS/SUBSCRIPTION_ELEMENT.PY

# ## PACKAGE IMPORTS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from .model_enums import SubscriptionElementStatus, SubscriptionElementKeep
from .error import Error
from .base import JsonModel, IntEnum, BlobMD5, EpochTimestamp, register_enum_column


# ## CLASSES

class SubscriptionElement(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    subscription_id = DB.Column(DB.Integer, DB.ForeignKey('subscription.id'), nullable=False, index=True)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=True)
    illust_url_id = DB.Column(DB.Integer, DB.ForeignKey('illust_url.id'), nullable=False)
    md5 = DB.Column(BlobMD5(nullable=True), nullable=True)
    keep_id = DB.Column(IntEnum, DB.ForeignKey('subscription_element_keep.id'), nullable=True)
    expires = DB.Column(EpochTimestamp(nullable=True), nullable=True)
    status_id = DB.Column(IntEnum, DB.ForeignKey('subscription_element_status.id'), nullable=False)

    # ## Relationships
    errors = DB.relationship(Error, lazy=True, uselist=True, cascade='all,delete',
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

    @classproperty(cached=False)
    def repr_attributes(cls):
        return ['id', 'subscription_id', 'post_id', 'illust_url_id', 'md5', 'expires', 'keep', 'status']

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
    register_enum_column(SubscriptionElement, SubscriptionElementStatus, 'status')
    register_enum_column(SubscriptionElement, SubscriptionElementKeep, 'keep')
