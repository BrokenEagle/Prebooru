# APP/MODELS/ERROR.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel, integer_column, text_column, timestamp_column


# ## CLASSES

class Error(JsonModel):
    # #### Columns
    id = integer_column(primary_key=True)
    module = text_column(nullable=False)
    message = text_column(nullable=False)
    created = timestamp_column(nullable=False)
    post_id = integer_column(foreign_key='post.id', nullable=True)
    subscription_id = integer_column(foreign_key='subscription.id', nullable=True)
    subscription_element_id = integer_column(foreign_key='subscription_element.id', nullable=True)
    download_id = integer_column(foreign_key='download.id', nullable=True)
    download_element_id = integer_column(foreign_key='download_element.id', nullable=True)
    upload_id = integer_column(foreign_key='upload.id', nullable=True)

    # ## Relations
    # (OtO) post [Post]
    # (OtO) subscription [Subscription]
    # (OtO) subscription_element [SubscriptionElement]
    # (OtO) upload [Upload]

    @memoized_property
    def append_type(self):
        if self.post_id is not None:
            return 'post'
        if self.upload_id is not None:
            return 'upload'
        if self.download_id is not None:
            return 'download'
        if self.download_element_id is not None:
            return 'download_element'
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
            "((post_id IS NULL) + (subscription_id IS NULL) + (subscription_element_id IS NULL) + (upload_id IS NULL) + (download_id IS NULL) + (download_element_id IS NULL)) in (5, 6)",  # noqa: E501
            name="attachments"),
    )


# ## INITIALIZATION

def initialize():
    DB.Index(None, Error.post_id, unique=False, sqlite_where=Error.post_id.is_not(None))
    DB.Index(None, Error.subscription_id, unique=False, sqlite_where=Error.subscription_id.is_not(None))
    DB.Index(None, Error.subscription_element_id, unique=False, sqlite_where=Error.subscription_element_id.is_not(None))
    DB.Index(None, Error.download_id, unique=False, sqlite_where=Error.download_id.is_not(None))
    DB.Index(None, Error.download_element_id, unique=False, sqlite_where=Error.download_element_id.is_not(None))
    DB.Index(None, Error.upload_id, unique=False, sqlite_where=Error.upload_id.is_not(None))

    from .post import Post
    from .subscription import Subscription
    from .subscription_element import SubscriptionElement
    from .download import Download
    from .download_element import DownloadElement
    from .upload import Upload
    # Access the opposite side of the relationship to force the back reference to be generated
    Post.errors.property._configure_started
    Subscription.errors.property._configure_started
    SubscriptionElement.errors.property._configure_started
    Download.errors.property._configure_started
    DownloadElement.errors.property._configure_started
    Upload.errors.property._configure_started
    Error.set_relation_properties()
