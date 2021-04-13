# APP/MODELS/UPLOAD.PY

# ##PYTHON IMPORTS
import datetime
from typing import List
from dataclasses import dataclass
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

# ##LOCAL IMPORTS
from .. import DB
from ..logical.utility import UniqueObjects
from ..base_model import JsonModel, IntOrNone, StrOrNone
from .upload_url import UploadUrl
from .post import Post
from .error import Error

# ##GLOBAL VARIABLES

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


# Classes


@dataclass
class Upload(JsonModel):
    # ## Declarations

    # #### JSON format
    id: int
    subscription_id: IntOrNone
    request_url: StrOrNone
    media_filepath: StrOrNone
    sample_filepath: StrOrNone
    illust_url_id: IntOrNone
    type: str
    status: str
    successes: int
    failures: int
    image_urls: List
    post_ids: List[int]
    errors: List
    created: datetime.datetime.isoformat

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
    subscription_id = DB.Column(DB.Integer, DB.ForeignKey('subscription.id'), nullable=True)
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)

    # #### Relationships
    image_urls = DB.relationship(UploadUrl, secondary=UploadUrls, lazy=True, uselist=True, backref=DB.backref('upload', lazy=True, uselist=False), cascade='all,delete')
    posts = DB.relationship(Post, secondary=UploadPosts, backref=DB.backref('uploads', lazy=True), lazy=True)
    errors = DB.relationship(Error, secondary=UploadErrors, lazy=True, cascade='all,delete')

    # #### Association proxies
    post_ids = association_proxy('posts', 'id')

    # ## Property methods

    @property
    def site_id(self):
        return self._source.SITE_ID

    @memoized_property
    def site_illust_id(self):
        if self.request_url:
            return self._source.GetIllustId(self.request_url)
        elif self.illust_url.id:
            return self.illust_url.illust.site_illust_id
        raise Exception("Unable to find site illust ID for upload #%d" % self.id)

    @memoized_property
    def illust(self):
        if len(self.posts) == 0:
            return None
        illusts = UniqueObjects(sum([post.illusts for post in self.posts], []))
        return next(filter(lambda x: (x.site_id == self.site_id) and (x.site_illust_id == self.site_illust_id), illusts), None)

    @memoized_property
    def artist(self):
        return self.illust.artist if self.illust is not None else None

    # #### Private

    @memoized_property
    def _source(self):
        from ..sources.base_source import GetPostSource, GetSourceById
        if self.request_url:
            return GetPostSource(self.request_url)
        elif self.illust_url_id:
            return GetSourceById(self.illust_url.site_id)
        raise Exception("Unable to find source for upload #%d" % self.id)

    # ## Class properties

    basic_attributes = ['id', 'successes', 'failures', 'subscription_id', 'illust_url_id', 'request_url', 'type', 'status', 'media_filepath', 'sample_filepath', 'created']
    relation_attributes = ['image_urls', 'posts', 'errors']
    searchable_attributes = basic_attributes + relation_attributes
