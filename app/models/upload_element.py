# APP/MODELS/UPLOAD_ELEMENT.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.ext.associationproxy import association_proxy

# ## LOCAL IMPORTS
from .. import DB
from ..enum_imports import upload_element_status
from .media_asset import MediaAsset
from .error import Error
from .base import JsonModel, BlobMD5, get_relation_definitions


# ## CLASSES

class UploadElement(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    upload_id = DB.Column(DB.Integer, DB.ForeignKey('upload.id'), nullable=False, index=True)
    illust_url_id = DB.Column(DB.Integer, DB.ForeignKey('illust_url.id'), nullable=False)
    #md5 = DB.Column(BlobMD5(nullable=True), nullable=True)
    status, status_id, status_name, status_enum, status_filter, status_col =\
        get_relation_definitions(upload_element_status, relname='status', relcol='id', colname='status_id',
                                 tblname='upload_element', nullable=False)
    media_asset_id = DB.Column(DB.INTEGER, DB.ForeignKey('media_asset.id'), nullable=True)

    # ## Relationships
    media = DB.relationship(MediaAsset, lazy='selectin', uselist=False,
                            backref=DB.backref('upload_element', lazy=True, uselist=False))
    errors = DB.relationship(Error, lazy=True, uselist=True, cascade='all,delete',
                             backref=DB.backref('upload_element', lazy=True, uselist=False))
    # (MtO) upload [Upload]
    # (MtO) illust_url [IllustUrl]

    # ## Association proxies
    md5 = association_proxy('media', 'md5')
    post = association_proxy('illust_url', 'post')

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
    #DB.Index(None, UploadElement.md5, unique=False, sqlite_where=UploadElement.md5.is_not(None))
    # Access the opposite side of the relationship to force the back reference to be generated
    Upload.elements.property._configure_started
    UploadElement.set_relation_properties()
