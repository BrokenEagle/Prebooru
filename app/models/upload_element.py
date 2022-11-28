# APP/MODELS/SUBSCRIPTION_ELEMENT.PY

# ## LOCAL IMPORTS
from .. import DB
from ..logical.enums import UploadElementStatusEnum
from .error import Error
from .base import JsonModel, IntEnum, BlobMD5, secondarytable


# ## GLOBAL VARIABLES

# Many-to-many tables

UploadElementErrors = secondarytable(
    'upload_element_errors',
    DB.Column('upload_element_id', DB.Integer, DB.ForeignKey('upload_element.id'), primary_key=True),
    DB.Column('error_id', DB.Integer, DB.ForeignKey('error.id'), primary_key=True),
    DB.Index(None, 'error_id', 'upload_element_id'),
)


# ## CLASSES

class UploadElement(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    upload_id = DB.Column(DB.Integer, DB.ForeignKey('upload.id'), nullable=False, index=True)
    illust_url_id = DB.Column(DB.Integer, DB.ForeignKey('illust_url.id'), nullable=False)
    md5 = DB.Column(BlobMD5(nullable=True), nullable=True)
    status = DB.Column(IntEnum(UploadElementStatusEnum), nullable=False)

    # ## Relationships
    errors = DB.relationship(Error, secondary=UploadElementErrors, lazy=True, cascade='all,delete',
                             backref=DB.backref('upload_element', uselist=False, lazy=True))
    # (MtO) upload [Upload]
    # (MtO) illust_url [IllustUrl]

    # ## Instance properties

    @property
    def duplicate_elements(self):
        return self._duplicate_element_query.all()

    def duplicate_posts(self):
        return self._duplicate_posts_query.all()

    @property
    def duplicate_element_count(self):
        return self._duplicate_element_query.get_count()

    @property
    def duplicate_post_count(self):
        return self._duplicate_post_query.get_count()

    # ## Class properties

    status_enum = UploadElementStatusEnum

    # ## Private

    @property
    def _duplicate_element_query(self):
        from .subscription_element import SubscriptionElement
        return SubscriptionElement.query.filter_by(md5=self.md5)

    @property
    def _duplicate_post_query(self):
        from .post import Post
        return Post.query.filter_by(md5=self.md5)


# ## INITIALIZATION

def initialize():
    from .upload import Upload
    DB.Index(None, UploadElement.md5, unique=False, sqlite_where=UploadElement.md5.is_not(None))
    # Access the opposite side of the relationship to force the back reference to be generated
    Upload.elements.property._configure_started
    UploadElement.set_relation_properties()
