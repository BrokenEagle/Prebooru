# APP/MODELS/SUBSCRIPTION_ELEMENT.PY

# ## LOCAL IMPORTS
from .. import DB
from .error import Error
from .base import JsonModel, NormalizedDatetime, secondarytable


# ## GLOBAL VARIABLES

# Many-to-many tables

SubscriptionElementErrors = secondarytable(
    'subscription_element_errors',
    DB.Column('subscription_element_id', DB.Integer, DB.ForeignKey('subscription_element.id'),
              primary_key=True),
    DB.Column('error_id', DB.Integer, DB.ForeignKey('error.id'), primary_key=True),
)


# ## CLASSES

class SubscriptionElement(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    subscription_id = DB.Column(DB.Integer, DB.ForeignKey('subscription.id'), nullable=False)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=True)
    illust_url_id = DB.Column(DB.Integer, DB.ForeignKey('illust_url.id'), nullable=False)
    md5 = DB.Column(DB.String(32), nullable=True)
    keep = DB.Column(DB.String(16), nullable=True)
    expires = DB.Column(NormalizedDatetime(), nullable=True)
    status = DB.Column(DB.String(16), nullable=True)
    deleted = DB.Column(DB.Boolean, nullable=False)
    active = DB.Column(DB.Boolean, nullable=False)

    # #### Relationships
    # subscription <- Susbscription (MtO)
    errors = DB.relationship(Error, secondary=SubscriptionElementErrors, lazy=True, cascade='all,delete',
                             backref=DB.backref('subscription_element', uselist=False, lazy=True))


# ## INITIALIZATION

def initialize():
    from .subscription import Subscription
    # Access the opposite side of the relationship to force the back reference to be generated
    Subscription.elements.property._configure_started
    SubscriptionElement.set_relation_properties()
