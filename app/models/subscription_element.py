# APP/MODELS/SUBSCRIPTION_ELEMENT.PY

# ## PACKAGE IMPORTS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from .model_enums import SubscriptionElementStatus, SubscriptionElementKeep
from .error import Error
from .base import JsonModel, integer_column, enum_column, md5_column, timestamp_column, register_enum_column,\
    relationship, backref


# ## CLASSES

class SubscriptionElement(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    subscription_id = integer_column(foreign_key='subscription.id', nullable=False, index=True)
    post_id = integer_column(foreign_key='post.id', nullable=True)
    illust_url_id = integer_column(foreign_key='illust_url.id', nullable=False)
    md5 = md5_column(nullable=True)
    keep_id = enum_column(foreign_key='subscription_element_keep.id', nullable=True)
    status_id = enum_column(foreign_key='subscription_element_status.id', nullable=False)
    expires = timestamp_column(nullable=True)

    # ## Relationships
    errors = relationship(Error, uselist=True, cascade='all,delete',
                          backref=backref('subscription_element', uselist=False))
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
