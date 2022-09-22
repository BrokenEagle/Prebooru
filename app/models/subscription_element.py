# APP/MODELS/SUBSCRIPTION_ELEMENT.PY

# ## PYTHON IMPORTS
import enum

# ## LOCAL IMPORTS
from .. import DB
from .error import Error
from .base import JsonModel, IntEnum, NormalizedDatetime, secondarytable, classproperty


# ## GLOBAL VARIABLES

# Many-to-many tables

SubscriptionElementErrors = secondarytable(
    'subscription_element_errors',
    DB.Column('subscription_element_id', DB.Integer, DB.ForeignKey('subscription_element.id'),
              primary_key=True),
    DB.Column('error_id', DB.Integer, DB.ForeignKey('error.id'), primary_key=True),
)


# ## CLASSES

class SubscriptionElementStatus(enum.Enum):
    active = enum.auto()
    unlinked = enum.auto()
    deleted = enum.auto()
    archived = enum.auto()
    error = enum.auto()
    duplicate = enum.auto()

    @classproperty(cached=False)
    def names(cls):
        return [e.name for e in cls]

    @classproperty(cached=False)
    def values(cls):
        return [e.value for e in cls]


class SubscriptionElement(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    subscription_id = DB.Column(DB.Integer, DB.ForeignKey('subscription.id'), nullable=False, index=True)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=True)
    illust_url_id = DB.Column(DB.Integer, DB.ForeignKey('illust_url.id'), nullable=False)
    md5 = DB.Column(DB.String(32), nullable=True)
    keep = DB.Column(DB.String(16), nullable=True)
    expires = DB.Column(NormalizedDatetime(), nullable=True)
    status = DB.Column(IntEnum(SubscriptionElementStatus), nullable=False)
    deleted = DB.Column(DB.Boolean, nullable=False)
    active = DB.Column(DB.Boolean, nullable=False)

    # #### Relationships
    # subscription <- Susbscription (MtO)
    errors = DB.relationship(Error, secondary=SubscriptionElementErrors, lazy=True, cascade='all,delete',
                             backref=DB.backref('subscription_element', uselist=False, lazy=True))
    # ## Class properties

    status_enum = SubscriptionElementStatus


# ## INITIALIZATION

def initialize():
    from .subscription import Subscription
    # Access the opposite side of the relationship to force the back reference to be generated
    Subscription.elements.property._configure_started
    SubscriptionElement.set_relation_properties()
