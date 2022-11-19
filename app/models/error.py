# APP/MODELS/ERROR.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel, EpochTimestamp


# ## CLASSES

class Error(JsonModel):
    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    module = DB.Column(DB.String(255), nullable=False)
    message = DB.Column(DB.UnicodeText, nullable=False)
    created = DB.Column(EpochTimestamp(nullable=False), nullable=False)

    # ## Relations
    # (OtO) post [Post]
    # (OtO) subscription [Subscription]
    # (OtO) subscription_element [SubscriptionElement]
    # (OtO) upload [Upload]
    # (OtO) upload_element [UploadElement]

    @memoized_property
    def append_item(self):
        return self.upload or self.upload_element or self.post or self.subscription or self.subscription_element
