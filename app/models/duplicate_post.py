# APP/MODELS/POOL_ELEMENT.PY

# ## PYTHON IMPORTS
import enum

# ## PACKAGE IMPORTS
from config import DEFAULT_PAGINATE_LIMIT

# ## LOCAL IMPORTS
from .. import DB, SESSION
from .base import JsonModel, ModelEnum, IntEnum


# ## FUNCTIONS

def duplicate_post_create(item):
    if item.__table__.name == 'upload':
        return UploadDuplicatePost(item=item)
    if item.__table__.name == 'subscription_element':
        return SubscriptionDuplicatePost(item=item)
    raise Exception("Invalid duplicate type.")


# ## CLASSES

class DuplicatePostType(ModelEnum):
    base = -1  # This should never actually be set
    upload = enum.auto()
    subscription = enum.auto()


class DuplicatePost(JsonModel):
    # ## Declarations

    # ## Class attributes

    polymorphic_base = True

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=False, index=True)
    upload_id = DB.Column(DB.Integer, DB.ForeignKey('upload.id'), nullable=True)
    subscription_element_id = DB.Column(DB.Integer, DB.ForeignKey('subscription_element.id'), nullable=True)
    type = DB.Column(IntEnum(DuplicatePostType), nullable=False)

    # ## Relationships
    # duplicates <- Post (MtO)

    # ## Class properties

    type_enum = DuplicatePostType

    # #### Private
    __mapper_args__ = {
        'polymorphic_identity': DuplicatePostType.base,
        'polymorphic_on': type,
    }
    __table_args__ = (
        DB.CheckConstraint("subscription_element_id IS NOT NULL OR upload_id IS NOT NULL", name="null_check"),
        {'sqlite_with_rowid': False,},
    )


class UploadDuplicatePost(DuplicatePost):
    # ## Declarations

    # ## Class attributes

    polymorphic_base = False

    # ## Relationships
    # duplicates <- Upload (MtO)

    # #### Private
    __mapper_args__ = {
        'polymorphic_identity': DuplicatePostType.upload,
    }


class SubscriptionDuplicatePost(DuplicatePost):
    # ## Declarations

    # ## Class attributes

    polymorphic_base = False

    # ## Relationships
    # duplicate <- SubscriptionElement (OtO)

    # #### Private
    __mapper_args__ = {
        'polymorphic_identity': DuplicatePostType.subscription,
    }


# ## INITIALIZATION

def initialize():
    DB.Index(None, DuplicatePost.upload_id, DuplicatePost.post_id, unique=True, sqlite_where=DuplicatePost.upload_id.is_not(None))
    DB.Index(None, DuplicatePost.subscription_element_id, DuplicatePost.post_id, unique=True, sqlite_where=DuplicatePost.subscription_element_id.is_not(None))
    DuplicatePost.polymorphic_columns = {
        'upload_id': UploadDuplicatePost,
        'subscription_element_id': SubscriptionDuplicatePost,
    }
    DuplicatePost.polymorphic_relations = {
        'upload': UploadDuplicatePost,
        'subscription_element': SubscriptionDuplicatePost,
    }
