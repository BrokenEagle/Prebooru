# APP/MODELS/SUBSCRIPTION_ELEMENT.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.ext.associationproxy import association_proxy

# ## LOCAL IMPORTS
from .. import DB
from ..enum_imports import subscription_element_status, subscription_element_keep
from .media_asset import MediaAsset
from .error import Error
from .base import JsonModel, BlobMD5, EpochTimestamp, get_relation_definitions


# ## CLASSES

class SubscriptionElement(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    subscription_id = DB.Column(DB.Integer, DB.ForeignKey('subscription.id'), nullable=False, index=True)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=True)
    illust_url_id = DB.Column(DB.Integer, DB.ForeignKey('illust_url.id'), nullable=False)
    #md5 = DB.Column(BlobMD5(nullable=True), nullable=True)
    keep, keep_id, keep_name, keep_enum, keep_filter, keep_col =\
        get_relation_definitions(subscription_element_keep, relname='keep', relcol='id', colname='keep_id',
                                 tblname='subscription_element', nullable=True)
    expires = DB.Column(EpochTimestamp(nullable=True), nullable=True)
    status, status_id, status_name, status_enum, status_filter, status_col =\
        get_relation_definitions(subscription_element_status, relname='status', relcol='id', colname='status_id',
                                 tblname='subscription_element', nullable=False)
    media_asset_id = DB.Column(DB.INTEGER, DB.ForeignKey('media_asset.id'), nullable=True)

    # ## Relationships
    media = DB.relationship(MediaAsset, lazy='selectin', uselist=False,
                            backref=DB.backref('subscription_elements', lazy=True, uselist=True))
    errors = DB.relationship(Error, lazy=True, uselist=True, cascade='all,delete',
                             backref=DB.backref('subscription_element', lazy=True, uselist=False))
    # (MtO) subscription [Susbscription]
    # (MtO) post [Post]
    # (OtO) illust_url [IllustUrl]

    # ## Association proxies
    md5 = association_proxy('media', 'md5')

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
        return SubscriptionElement.query.join(MediaAsset)\
                                        .filter(MediaAsset.md5 == self.md5,
                                                SubscriptionElement.id != self.id)


# ## INITIALIZATION

def initialize():
    from .subscription import Subscription
    #DB.Index(None, SubscriptionElement.md5, unique=False, sqlite_where=SubscriptionElement.md5.is_not(None))
    DB.Index(None, SubscriptionElement.post_id, unique=True, sqlite_where=SubscriptionElement.post_id.is_not(None))
    # Access the opposite side of the relationship to force the back reference to be generated
    Subscription.elements.property._configure_started
    SubscriptionElement.set_relation_properties()
