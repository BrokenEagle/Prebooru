# APP/MODELS/UPLOAD.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property

# ## PACKAGE IMPORTS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..logical.enums import UploadStatusEnum
from ..logical.batch_loader import selectinload_batch_primary, selectinload_batch_secondary
from .upload_url import UploadUrl
from .upload_element import UploadElement
from .illust_url import IllustUrl
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

class Upload(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    request_url = DB.Column(DB.String(255), nullable=True)
    successes = DB.Column(DB.Integer, nullable=False)
    failures = DB.Column(DB.Integer, nullable=False)
    status = DB.Column(IntEnum(UploadStatusEnum), nullable=False)
    media_filepath = DB.Column(DB.String(255), nullable=True)
    sample_filepath = DB.Column(DB.String(255), nullable=True)
    illust_url_id = DB.Column(DB.Integer, DB.ForeignKey('illust_url.id'), nullable=True)
    created = DB.Column(EpochTimestamp(nullable=False), nullable=False)

    # ## Relationships
    image_urls = DB.relationship(UploadUrl, secondary=UploadUrls, lazy=True, uselist=True, cascade='all,delete',
                                 backref=DB.backref('upload', lazy=True, uselist=False))
    errors = DB.relationship(Error, secondary=UploadErrors, lazy=True, cascade='all,delete',
                             backref=DB.backref('upload', uselist=False, lazy=True))
    elements = DB.relationship(UploadElement, lazy=True, cascade='all,delete',
                               backref=DB.backref('upload', uselist=False, lazy=True))
    file_illust_url = DB.relationship(IllustUrl, lazy=True, uselist=False, viewonly=True,
                                      backref=DB.backref('upload', lazy=True, uselist=False))

    # ## Instance properties

    @memoized_property
    def illust_urls(self):
        self._populate_illust_urls()
        return self._illust_urls

    @memoized_property
    def duplicate_illust_urls(self):
        self._populate_illust_urls()
        return self._duplicate_illust_urls

    @property
    def posts(self):
        self._populate_posts()
        return [illust_url.post for illust_url in self.illust_urls if illust_url.post is not None]

    @property
    def duplicate_posts(self):
        self._populate_posts()
        return [illust_url.post for illust_url in self.duplicate_illust_urls if illust_url.post is not None]

    @property
    def post_ids(self):
        return [post.id for post in self.posts]

    @property
    def duplicate_post_ids(self):
        return [post.id for post in self.duplicate_posts]

    @property
    def site_id(self):
        return self._source.SITE_ID

    @memoized_property
    def site_illust_id(self):
        if self.request_url:
            return self._source.get_illust_id(self.request_url)
        elif self.illust is not None:
            return self.illust_url.illust.site_illust_id

    @memoized_property
    def illust(self):
        if self.illust_url_id is not None:
            return self.file_illust_url.illust
        if len(self.illust_urls):
            return self.illust_urls[0].illust

    @memoized_property
    def artist(self):
        if self.illust is not None:
            return self.illust.artist

    # ## Class properties

    status_enum = UploadStatusEnum

    @classproperty(cached=True)
    def json_attributes(cls):
        return super().json_attributes + ['image_urls', 'post_ids', 'duplicate_post_ids', 'errors']

    # ## Private

    @memoized_property
    def _source(self):
        from ..logical.sources.base import get_post_source, get_source_by_id
        if self.request_url:
            return get_post_source(self.request_url)
        elif self.illust_url_id:
            return get_source_by_id(self.illust_url.site_id)
        raise Exception("Unable to find source for upload #%d" % self.id)

    def _populate_illust_urls(self):
        if len(self.elements):
            selectinload_batch_primary(self.elements, 'illust_url')
        self._illust_urls = [element.illust_url for element in self.elements]
        self._duplicate_illust_urls = [element.illust_url for element in self.elements
                                       if element.status.name == 'duplicate']
        self._populate_illust_urls = lambda: None

    def _populate_posts(self):
        if len(self.illust_urls):
            selectinload_batch_secondary(self.illust_urls, 'post')
        self._populate_posts = lambda: None
