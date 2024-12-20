# APP/MODELS/UPLOAD.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property
from sqlalchemy.orm import lazyload

# ## PACKAGE IMPORTS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..enum_imports import upload_status
from ..logical.batch_loader import selectinload_batch_primary
from .upload_url import UploadUrl
from .upload_element import UploadElement
from .illust_url import IllustUrl
from .error import Error
from .base import JsonModel, EpochTimestamp, get_relation_definitions


# ## CLASSES

class Upload(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    request_url = DB.Column(DB.String(255), nullable=True)
    successes = DB.Column(DB.Integer, nullable=False)
    failures = DB.Column(DB.Integer, nullable=False)
    status, status_id, status_name, status_enum, status_filter, status_col =\
        get_relation_definitions(upload_status, relname='status', relcol='id', colname='status_id',
                                 tblname='upload', nullable=False)
    media_filepath = DB.Column(DB.String(255), nullable=True)
    sample_filepath = DB.Column(DB.String(255), nullable=True)
    illust_url_id = DB.Column(DB.Integer, DB.ForeignKey('illust_url.id'), nullable=True)
    created = DB.Column(EpochTimestamp(nullable=False), nullable=False)

    # ## Relationships
    image_urls = DB.relationship(UploadUrl, lazy=True, uselist=True, cascade='all,delete',
                                 backref=DB.backref('upload', lazy=True, uselist=False))
    errors = DB.relationship(Error, lazy=True, uselist=True, cascade='all,delete',
                             backref=DB.backref('upload', lazy=True, uselist=False))
    elements = DB.relationship(UploadElement, lazy=True, cascade='all,delete',
                               backref=DB.backref('upload', uselist=False, lazy=True))
    file_illust_url = DB.relationship(IllustUrl, lazy=True, uselist=False, viewonly=True,
                                      backref=DB.backref('file_uploads', lazy=True, uselist=True))

    # ## Instance properties

    def elements_paginate(self, page=None, per_page=None, options=None):
        def _get_options(options):
            if options is None:
                return (lazyload('*'),)
            if type(options) is tuple:
                return options
            return (options,)
        query = self._elements_query
        query = query.options(*_get_options(options))
        query = query.order_by(UploadElement.id.asc())
        return query.count_paginate(per_page=per_page, page=page)

    @memoized_property
    def illust_urls(self):
        self._populate_illust_urls()
        return self._illust_urls

    @memoized_property
    def complete_illust_urls(self):
        self._populate_illust_urls()
        return self._complete_illust_urls

    @memoized_property
    def duplicate_illust_urls(self):
        self._populate_illust_urls()
        return self._duplicate_illust_urls

    @property
    def type(self):
        if len(self.illust_urls):
            return 'network'
        if self.illust_url_id is not None:
            return 'file'
        return 'unknown'

    @property
    def posts(self):
        if self.type == 'network':
            self._populate_posts()
            return [illust_url.post for illust_url in self.illust_urls if illust_url.post is not None]
        elif self.type == 'file':
            return [self.file_illust_url.post] if self.file_illust_url.post is not None else []
        return []

    @property
    def complete_posts(self):
        if self.type == 'network':
            self._populate_posts()
            return [illust_url.post for illust_url in self.complete_illust_urls if illust_url.post is not None]
        elif self.type == 'file':
            return self.posts if self.status.name == 'complete' else []
        return []

    @property
    def duplicate_posts(self):
        if self.type == 'network':
            self._populate_posts()
            return [illust_url.post for illust_url in self.duplicate_illust_urls if illust_url.post is not None]
        elif self.type == 'file':
            return self.posts if self.status.name == 'duplicate' else []
        return []

    @property
    def post_ids(self):
        return [post.id for post in self.posts]

    @property
    def complete_post_ids(self):
        return [post.id for post in self.complete_posts]

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

    @property
    def illust_id(self):
        return getattr(self.illust, 'id', None)

    @memoized_property
    def artist(self):
        return getattr(self.illust, 'artist', None)

    @property
    def artist_id(self):
        return getattr(self.artist, 'id', None)

    # ## Class properties

    @classproperty(cached=True)
    def json_attributes(cls):
        return\
            super().json_attributes +\
            ['image_urls', 'post_ids', 'complete_post_ids', 'duplicate_post_ids', 'illust_id', 'artist_id', 'errors']

    # ## Private

    @property
    def _elements_query(self):
        return UploadElement.query.filter_by(upload_id=self.id)

    @memoized_property
    def _source(self):
        from ..logical.sources.base_src import get_post_source
        if self.request_url:
            return get_post_source(self.request_url)
        elif self.illust_url_id:
            return self.illust_url.site.source
        raise Exception("Unable to find source for upload #%d" % self.id)

    def _populate_illust_urls(self):
        if len(self.elements):
            selectinload_batch_primary(self.elements, 'illust_url')
        self._illust_urls = [element.illust_url for element in self.elements]
        self._complete_illust_urls = [element.illust_url for element in self.elements
                                      if element.status.name == 'complete']
        self._duplicate_illust_urls = [element.illust_url for element in self.elements
                                       if element.status.name == 'duplicate']
        self._populate_illust_urls = lambda: None

    def _populate_posts(self):
        selectinload_batch_primary(self.illust_urls, 'post')
        self._populate_posts = lambda: None
