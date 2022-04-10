# APP/MODELS/SUBSCRIPTION_POOL.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property

# ## LOCAL IMPORTS
from .. import DB
from .error import Error
from .base import JsonModel


# ## GLOBAL VARIABLES

# Many-to-many tables

SubscriptionPoolErrors = DB.Table(
    'subscription_pool_errors',
    DB.Column('subscription_pool_id', DB.Integer, DB.ForeignKey('subscription_pool.id'), primary_key=True),
    DB.Column('error_id', DB.Integer, DB.ForeignKey('error.id'), primary_key=True),
)


# ## CLASSES

class SubscriptionPool(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    artist_id = DB.Column(DB.Integer, DB.ForeignKey('artist.id'), nullable=False)
    interval = DB.Column(DB.Float, nullable=False)
    expiration = DB.Column(DB.Float, nullable=True)
    status = DB.Column(DB.String(31), nullable=False)
    last_id = DB.Column(DB.Integer, nullable=True)
    requery = DB.Column(DB.DateTime(timezone=False), nullable=True)
    checked = DB.Column(DB.DateTime(timezone=False), nullable=True)
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)
    updated = DB.Column(DB.DateTime(timezone=False), nullable=False)
    active = DB.Column(DB.Boolean, nullable=False)

    # #### Relationships
    errors = DB.relationship(Error, secondary=SubscriptionPoolErrors, lazy=True, cascade='all,delete',
                             backref=DB.backref('subscription_pool', uselist=False, lazy=True))

    # ## Class properties

    basic_attributes = ['id', 'artist_id', 'interval', 'expiration', 'requery', 'checked', 'created', 'updated',
                        'active']
    json_attributes = basic_attributes
    searchable_attributes = basic_attributes


# ## INITIALIZATION

def initialize():
    from .artist import Artist
    # Access the opposite side of the relationship to force the back reference to be generated
    Artist.subscription_pool.property._configure_started
    SubscriptionPool.set_relation_properties()
