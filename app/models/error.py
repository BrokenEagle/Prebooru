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
    def append_type(self):
        if self.post_id is not None:
            return 'post'
        if self.upload_id is not None:
            return 'upload'
        if self.upload_element_id is not None:
            return 'upload_element'
        if self.subscription_id is not None:
            return 'subscription'
        if self.subscription_element_id is not None:
            return 'subscription_element'

    @memoized_property
    def append_item(self):
        if self.append_type is not None:
            return getattr(self, self.append_type)

    @property
    def append_shortlink(self):
        if self.append_type is not None:
            return getattr(self, self.append_type + '_shortlink')

    @property
    def append_show_url(self):
        if self.append_type is not None:
            return getattr(self, self.append_type + '_show_url')

    @property
    def append_show_link(self):
        if self.append_type is not None:
            return getattr(self, self.append_type + '_show_link')

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

    from .post import Post
    from .subscription import Subscription
    from .subscription_element import SubscriptionElement
    from .upload import Upload
    from .upload_element import UploadElement
    # Access the opposite side of the relationship to force the back reference to be generated
    Post.errors.property._configure_started
    Subscription.errors.property._configure_started
    SubscriptionElement.errors.property._configure_started
    Upload.errors.property._configure_started
    UploadElement.errors.property._configure_started
    Error.set_relation_properties()
