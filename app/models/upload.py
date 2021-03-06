# APP/MODELS/UPLOAD.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

# ## LOCAL IMPORTS
from .. import DB
from ..logical.utility import unique_objects
from .upload_url import UploadUrl
from .post import Post
from .error import Error
from .base import JsonModel, classproperty


# ## GLOBAL VARIABLES

# Many-to-many tables

UploadUrls = DB.Table(
    'upload_urls',
    DB.Column('upload_id', DB.Integer, DB.ForeignKey('upload.id'), primary_key=True),
    DB.Column('upload_url_id', DB.Integer, DB.ForeignKey('upload_url.id'), primary_key=True),
)
UploadErrors = DB.Table(
    'upload_errors',
    DB.Column('upload_id', DB.Integer, DB.ForeignKey('upload.id'), primary_key=True),
    DB.Column('error_id', DB.Integer, DB.ForeignKey('error.id'), primary_key=True),
)
UploadPosts = DB.Table(
    'upload_posts',
    DB.Column('upload_id', DB.Integer, DB.ForeignKey('upload.id'), primary_key=True),
    DB.Column('post_id', DB.Integer, DB.ForeignKey('post.id'), primary_key=True),
)


# ## CLASSES

class Upload(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    request_url = DB.Column(DB.String(255), nullable=True)
    successes = DB.Column(DB.Integer, nullable=False)
    failures = DB.Column(DB.Integer, nullable=False)
    type = DB.Column(DB.String(255), nullable=False)
    status = DB.Column(DB.String(255), nullable=False)
    media_filepath = DB.Column(DB.String(255), nullable=True)
    sample_filepath = DB.Column(DB.String(255), nullable=True)
    illust_url_id = DB.Column(DB.Integer, DB.ForeignKey('illust_url.id'), nullable=True)
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)

    # #### Relationships
    image_urls = DB.relationship(UploadUrl, secondary=UploadUrls, lazy=True, uselist=True, cascade='all,delete',
                                 backref=DB.backref('upload', lazy=True, uselist=False))
    posts = DB.relationship(Post, secondary=UploadPosts, lazy=True, backref=DB.backref('uploads', lazy=True))
    errors = DB.relationship(Error, secondary=UploadErrors, lazy=True, cascade='all,delete',
                             backref=DB.backref('upload', uselist=False, lazy=True))

    # #### Association proxies
    post_ids = association_proxy('posts', 'id')

    # ## Property methods

    @property
    def site_id(self):
        return self._source.SITE_ID

    @memoized_property
    def site_illust_id(self):
        if self.request_url:
            return self._source.get_illust_id(self.request_url)
        elif self.illust_url.id:
            return self.illust_url.illust.site_illust_id
        raise Exception("Unable to find site illust ID for upload #%d" % self.id)

    @memoized_property
    def illust(self):
        if len(self.posts) == 0:
            return None
        illusts = unique_objects(sum([post.illusts for post in self.posts], []))
        return next(filter(lambda x: (x.site_id == self.site_id) and (x.site_illust_id == self.site_illust_id),
                           illusts), None)

    @memoized_property
    def artist(self):
        return self.illust.artist if self.illust is not None else None

    # #### Private

    @memoized_property
    def _source(self):
        from ..logical.sources.base import get_post_source, get_source_by_id
        if self.request_url:
            return get_post_source(self.request_url)
        elif self.illust_url_id:
            return get_source_by_id(self.illust_url.site_id)
        raise Exception("Unable to find source for upload #%d" % self.id)

    # ## Class properties

    @classproperty(cached=True)
    def json_attributes(cls):
        return super().json_attributes + ['image_urls', 'post_ids', 'errors']
