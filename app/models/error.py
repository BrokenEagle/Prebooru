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
    module = DB.Column(DB.Text, nullable=False)
    message = DB.Column(DB.UnicodeText, nullable=False)
    created = DB.Column(EpochTimestamp(nullable=False), nullable=False)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=True)
    subscription_id = DB.Column(DB.Integer, DB.ForeignKey('subscription.id'), nullable=True)
    subscription_element_id = DB.Column(DB.Integer, DB.ForeignKey('subscription_element.id'), nullable=True)
    upload_id = DB.Column(DB.Integer, DB.ForeignKey('upload.id'), nullable=True)
    upload_element_id = DB.Column(DB.Integer, DB.ForeignKey('upload_element.id'), nullable=True)

    # ## Relations
    # (OtO) post [Post]
    # (OtO) subscription [Subscription]
    # (OtO) subscription_element [SubscriptionElement]
    # (OtO) upload [Upload]
    # (OtO) upload_element [UploadElement]

    @memoized_property
    def append_item(self):
        return self.upload or self.upload_element or self.post or self.subscription or self.subscription_element

    __table_args__ = (
        DB.CheckConstraint(
            "((upload_element_id IS NULL) + (subscription_id IS NULL) + "
            + "(subscription_element_id IS NULL) + (upload_id IS NULL) + "
            + "(upload_element_id IS NULL)) in (4, 5)",
            name="attachments"),
    )


# ## INITIALIZATION

def initialize():
    DB.Index(None, Error.post_id, unique=False, sqlite_where=Error.post_id.is_not(None))
    DB.Index(None, Error.subscription_id, unique=False, sqlite_where=Error.subscription_id.is_not(None))
    DB.Index(None, Error.subscription_element_id, unique=False, sqlite_where=Error.subscription_element_id.is_not(None))
    DB.Index(None, Error.upload_id, unique=False, sqlite_where=Error.upload_id.is_not(None))
    DB.Index(None, Error.upload_element_id, unique=False, sqlite_where=Error.upload_element_id.is_not(None))
