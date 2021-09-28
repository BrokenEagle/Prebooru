# APP/MODELS/SUBSCRIPTION.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ## CLASSES

class Subscription(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    artist_id = DB.Column(DB.Integer, nullable=False)
    requery = DB.Column(DB.DateTime(timezone=False), nullable=True)
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)

    # #### Relationships
    uploads = DB.relationship('Upload', backref='subscription', lazy=True)

    # ## Class properties

    basic_attributes = ['id', 'artist_id', 'requery', 'created']
    json_attributes = basic_attributes
