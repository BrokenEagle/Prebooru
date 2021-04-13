# APP/MODELS/SUBSCRIPTION.PY

# ## PYTHON IMPORTS
import datetime
from dataclasses import dataclass

# ## LOCAL IMPORTS
from .. import DB
from ..base_model import JsonModel, DateTimeOrNull


# ## CLASSES

@dataclass
class Subscription(JsonModel):
    # ## Declarations

    # #### JSON format
    id: int
    artist_id: int
    requery: DateTimeOrNull
    created: datetime.datetime.isoformat

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    artist_id = DB.Column(DB.Integer, nullable=False)
    uploads = DB.relationship('Upload', backref='subscription', lazy=True)
    requery = DB.Column(DB.DateTime(timezone=False), nullable=True)
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)
