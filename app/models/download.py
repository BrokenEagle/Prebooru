# APP/MODELS/DOWNLOAD.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property
from sqlalchemy.orm import lazyload

# ## PACKAGE IMPORTS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..logical.batch_loader import selectinload_batch_primary
from .model_enums import DownloadStatus
from .download_url import DownloadUrl
from .download_element import DownloadElement
from .error import Error
from .base import JsonModel, IntEnum, EpochTimestamp, register_enum_column


# ## CLASSES

class Download(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    request_url = DB.Column(DB.TEXT, nullable=False)
    status_id = DB.Column(IntEnum, DB.ForeignKey('download_status.id'), nullable=False)
    created = DB.Column(EpochTimestamp(nullable=False), nullable=False)

    # ## Relationships
    image_urls = DB.relationship(DownloadUrl, lazy=True, uselist=True, cascade='all,delete',
                                 backref=DB.backref('download', lazy=True, uselist=False))
    errors = DB.relationship(Error, lazy=True, uselist=True, cascade='all,delete',
                             backref=DB.backref('download', lazy=True, uselist=False))
    elements = DB.relationship(DownloadElement, lazy=True, cascade='all,delete',
                               backref=DB.backref('download', uselist=False, lazy=True))

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
        query = query.order_by(DownloadElement.id.asc())
        return query.count_paginate(per_page=per_page, page=page)

    @memoized_property
    def complete_count(self):
        return self._elements_query.filter(DownloadElement.status_value == 'complete').get_count()

    @memoized_property
    def error_count(self):
        return self._elements_query.filter(DownloadElement.status_value == 'error').get_count()

    @memoized_property
    def other_count(self):
        return self._elements_query.filter(DownloadElement.status_value.not_in(['complete', 'error'])).get_count()

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
    def posts(self):
        self._populate_posts()
        return [illust_url.post for illust_url in self.illust_urls if illust_url.post is not None]

    @property
    def complete_posts(self):
        self._populate_posts()
        return [illust_url.post for illust_url in self.complete_illust_urls if illust_url.post is not None]

    @property
    def duplicate_posts(self):
        return [illust_url.post for illust_url in self.duplicate_illust_urls if illust_url.post is not None]

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
        return super().json_attributes +\
            ['image_urls', 'post_ids', 'complete_post_ids', 'duplicate_post_ids', 'illust_id', 'artist_id', 'errors']

    # ## Private

    @property
    def _elements_query(self):
        return DownloadElement.query.filter_by(download_id=self.id)

    @memoized_property
    def _source(self):
        from ..logical.sources.base_src import get_post_source
        return get_post_source(self.request_url)

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
        if len(self.illust_urls):
            selectinload_batch_primary(self.illust_urls, 'post')
        self._populate_posts = lambda: None


# ## Initialize

def initialize():
    register_enum_column(Download, DownloadStatus, 'status')
