# APP/MODELS/SUBSCRIPTION_POOL_ELEMENT.PY

# ## LOCAL IMPORTS
from .. import DB
from .error import Error
from .base import JsonModel, secondarytable


# ## GLOBAL VARIABLES

# Many-to-many tables

SubscriptionPoolElementErrors = secondarytable(
    'subscription_pool_element_errors',
    DB.Column('subscription_pool_element_id', DB.Integer, DB.ForeignKey('subscription_pool_element.id'),
              primary_key=True),
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
    keep = DB.Column(DB.String(16), nullable=True)
    expires = DB.Column(DB.DateTime(timezone=False), nullable=True)
    status = DB.Column(DB.String(16), nullable=True)
    deleted = DB.Column(DB.Boolean, nullable=False)
    active = DB.Column(DB.Boolean, nullable=False)

    # #### Relationships
    # pool <- SusbscriptionPool (MtO)
    errors = DB.relationship(Error, secondary=SubscriptionPoolElementErrors, lazy=True, cascade='all,delete',
                             backref=DB.backref('subscription_pool_element', uselist=False, lazy=True))


# ## INITIALIZATION

def initialize():
    from .subscription_pool import SubscriptionPool
    # Access the opposite side of the relationship to force the back reference to be generated
    SubscriptionPool.elements.property._configure_started
    SubscriptionPoolElement.set_relation_properties()
