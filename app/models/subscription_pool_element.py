# APP/MODELS/SUBSCRIPTION_POOL_ELEMENT.PY

# ## LOCAL IMPORTS
from .. import DB
from .error import Error
from .base import JsonModel


# ## GLOBAL VARIABLES

# Many-to-many tables

SubscriptionPoolElementErrors = DB.Table(
    'subscription_pool_element_errors',
    DB.Column('subscription_pool_element_id', DB.Integer, DB.ForeignKey('subscription_pool_element.id'), primary_key=True),
    DB.Column('error_id', DB.Integer, DB.ForeignKey('error.id'), primary_key=True),
)


# ## CLASSES

class SubscriptionPoolElement(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    pool_id = DB.Column(DB.Integer, DB.ForeignKey('subscription_pool.id'), nullable=False)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=True)
    illust_url_id = DB.Column(DB.Integer, DB.ForeignKey('illust_url.id'), nullable=False)
    md5 = DB.Column(DB.String(32), nullable=True)
    keep = DB.Column(DB.String(16), nullable=True) # Can have the values of yes, maybe, no, or null
    expires = DB.Column(DB.DateTime(timezone=False), nullable=True) # Will be deleted by the system after this date
    deleted = DB.Column(DB.Boolean, nullable=False) # Marked as deleted by the user, so that a post with the same MD5 won't be created again
    active = DB.Column(DB.Boolean, nullable=False) # Marked as inactive by the system, so that this particular element isn't downloaded again

    # #### Relationships
    # pool <- SusbscriptionPool (MtO)
    errors = DB.relationship(Error, secondary=SubscriptionPoolElementErrors, lazy=True, cascade='all,delete',
                             backref=DB.backref('subscription_pool_element', uselist=False, lazy=True))

    # ## Class properties

    basic_attributes = ['id', 'pool_id', 'post_id', 'illust_url_id', 'md5', 'keep', 'expires', 'deleted', 'active']
    json_attributes = basic_attributes
    relation_attributes = ['pool', 'post', 'illust_url']
    searchable_attributes = basic_attributes + relation_attributes


# ## INITIALIZATION

def initialize():
    from .subscription_pool import SubscriptionPool
    # Access the opposite side of the relationship to force the back reference to be generated
    SubscriptionPool.elements.property._configure_started
    SubscriptionPoolElement.set_relation_properties()
