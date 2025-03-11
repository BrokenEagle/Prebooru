# APP/MODELS/SUBSCRIPTION_ELEMENT.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from utility.obj import classproperty, memoized_classproperty
from utility.data import swap_list_values

# ## LOCAL IMPORTS
from .model_enums import SubscriptionElementStatus, SubscriptionElementKeep
from .error import Error
from .base import JsonModel, integer_column, enum_column, timestamp_column, register_enum_column,\
    relationship, backref


# ## CLASSES

class SubscriptionElement(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    subscription_id = integer_column(foreign_key='subscription.id', nullable=False, index=True)
    illust_url_id = integer_column(foreign_key='illust_url.id', nullable=False, index=True, unique=True)
    keep_id = enum_column(foreign_key='subscription_element_keep.id', nullable=True)
    status_id = enum_column(foreign_key='subscription_element_status.id', nullable=False)
    expires = timestamp_column(nullable=True)

    # ## Relationships
    errors = relationship(Error, uselist=True, cascade='all,delete',
                          backref=backref('subscription_element', uselist=False))
    # (MtO) subscription [Susbscription]
    # (OtO) illust_url [IllustUrl]

    # ## Association proxies
    post = association_proxy('illust_url', 'post')
    archive_post = association_proxy('illust_url', 'archive_post')

    # ## Instance properties

    @property
    def md5(self):
        return getattr(self.illust_url, 'md5', None)

    # ## Class properties

    @memoized_classproperty
    def repr_attributes(cls):
        mapping = {
            'status_id': ('status', 'status_name'),
            'keep_id': ('keep', 'keep_name'),
        }
        return swap_list_values(super().repr_attributes, mapping)

    @classproperty
    def json_attributes(cls):
        return cls.repr_attributes


# ## INITIALIZATION

def initialize():
    from .subscription import Subscription
    # Access the opposite side of the relationship to force the back reference to be generated
    Subscription.elements.property._configure_started
    SubscriptionElement.set_relation_properties()
    register_enum_column(SubscriptionElement, SubscriptionElementStatus, 'status')
    register_enum_column(SubscriptionElement, SubscriptionElementKeep, 'keep')
