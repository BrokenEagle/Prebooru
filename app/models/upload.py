# APP/MODELS/UPLOAD.PY

# ## PYTHON IMPORTS
import enum

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from utility.obj import AttrEnum, classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..logical.utility import unique_objects
from .upload_url import UploadUrl
from .upload_element import UploadElement
from .error import Error
from .base import JsonModel, IntEnum, EpochTimestamp, secondarytable


# ## GLOBAL VARIABLES

# Many-to-many tables

UploadUrls = secondarytable(
    'upload_urls',
    DB.Column('upload_id', DB.Integer, DB.ForeignKey('upload.id'), primary_key=True),
    DB.Column('upload_url_id', DB.Integer, DB.ForeignKey('upload_url.id'), primary_key=True),
)
UploadErrors = secondarytable(
    'upload_errors',
    DB.Column('upload_id', DB.Integer, DB.ForeignKey('upload.id'), primary_key=True),
    DB.Column('error_id', DB.Integer, DB.ForeignKey('error.id'), primary_key=True),
    DB.Index(None, 'error_id', 'upload_id'),
)


# ## CLASSES

class UploadStatus(AttrEnum):
    complete = enum.auto()
    pending = enum.auto()
    processing = enum.auto()
    duplicate = enum.auto()
    error = enum.auto()


class Upload(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    request_url = DB.Column(DB.String(255), nullable=True)
    successes = DB.Column(DB.Integer, nullable=False)
    failures = DB.Column(DB.Integer, nullable=False)
    status = DB.Column(IntEnum(UploadStatus), nullable=False)
    media_filepath = DB.Column(DB.String(255), nullable=True)
    sample_filepath = DB.Column(DB.String(255), nullable=True)
    illust_url_id = DB.Column(DB.Integer, DB.ForeignKey('illust_url.id'), nullable=True)
    created = DB.Column(EpochTimestamp(nullable=False), nullable=False)

    # #### Relationships
    image_urls = DB.relationship(UploadUrl, secondary=UploadUrls, lazy=True, uselist=True, cascade='all,delete',
                                 backref=DB.backref('upload', lazy=True, uselist=False))
    errors = DB.relationship(Error, secondary=UploadErrors, lazy=True, cascade='all,delete',
                             backref=DB.backref('upload', uselist=False, lazy=True))
    elements = DB.relationship(UploadElement, lazy=True, cascade='all,delete',
                               backref=DB.backref('upload', uselist=False, lazy=True))

    # #### Association proxies
    illust_urls = association_proxy('elements', 'illust_url')

    # ## Property methods

    @property
    def posts(self):
        return [illust_url.post for illust_url in self.illust_urls if illust_url.post is not None]

    @property
    def post_ids(self):
        return [post.id for post in self.posts]

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
        return next(filter(lambda x: (x.site_id.value == self.site_id) and (x.site_illust_id == self.site_illust_id),
                           illusts), None)

    @memoized_property
    def artist(self):
        return self.illust.artist if self.illust is not None else None

    # #### Private

    @memoized_property
    def _source(self):
        from ..logical.sources.base import get_post_source
        if self.request_url:
            return get_post_source(self.request_url)
        elif self.illust_url_id:
            return self.illust_url.site_id.source
        raise Exception("Unable to find source for upload #%d" % self.id)

    # ## Class properties

    status_enum = UploadStatus

    @classproperty(cached=True)
    def json_attributes(cls):
        return super().json_attributes + ['image_urls', 'post_ids', 'errors']
