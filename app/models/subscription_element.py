# APP/MODELS/SUBSCRIPTION_ELEMENT.PY

# ## PYTHON IMPORTS
import enum

# ## LOCAL IMPORTS
from .. import DB
from .error import Error
from .base import JsonModel, ModelEnum, IntEnum, BlobMD5, NormalizedDatetime, secondarytable


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

class SubscriptionElementStatus(ModelEnum):
    active = enum.auto()
    unlinked = enum.auto()
    deleted = enum.auto()
    archived = enum.auto()
    error = enum.auto()
    duplicate = enum.auto()


class SubscriptionElementKeep(ModelEnum):
    yes = enum.auto()
    no = enum.auto()
    maybe = enum.auto()
    archive = enum.auto()


class SubscriptionElement(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    subscription_id = DB.Column(DB.Integer, DB.ForeignKey('subscription.id'), nullable=False, index=True)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=True)
    illust_url_id = DB.Column(DB.Integer, DB.ForeignKey('illust_url.id'), nullable=False)
    md5 = DB.Column(BlobMD5(nullable=True), nullable=True)
    keep = DB.Column(IntEnum(SubscriptionElementKeep, nullable=True), nullable=True)
    expires = DB.Column(NormalizedDatetime(), nullable=True)
    status = DB.Column(IntEnum(SubscriptionElementStatus), nullable=False)

    # #### Relationships
    # subscription <- Susbscription (MtO)
    errors = DB.relationship(Error, secondary=SubscriptionElementErrors, lazy=True, cascade='all,delete',
                             backref=DB.backref('subscription_element', uselist=False, lazy=True))

    # #### Instance properties

    @property
    def duplicate_elements(self):
        return self._duplicate_element_query.all()

    @property
    def duplicate_element_count(self):
        return self._duplicate_element_query.get_count()

    # #### Class properties

    status_enum = SubscriptionElementStatus
    keep_enum = SubscriptionElementKeep

    # ## Private

    @property
    def _duplicate_element_query(self):
        return SubscriptionElement.query.filter(SubscriptionElement.md5 == self.md5, SubscriptionElement.id != self.id)


# ## INITIALIZATION

def initialize():
    from .subscription import Subscription
    DB.Index(None, SubscriptionElement.md5, unique=False, sqlite_where=SubscriptionElement.md5.is_not(None))
    DB.Index(None, SubscriptionElement.post_id, unique=False, sqlite_where=SubscriptionElement.post_id.is_not(None))
    # Access the opposite side of the relationship to force the back reference to be generated
    Subscription.elements.property._configure_started
    SubscriptionElement.set_relation_properties()
