# APP/MODELS/DOWNLOAD.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property
from sqlalchemy.orm import lazyload
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from utility.obj import memoized_classproperty
from utility.data import swap_list_values, dict_filter

# ## LOCAL IMPORTS
from ..logical.batch_loader import selectinload_batch_primary
from .model_enums import DownloadStatus
from .download_url import DownloadUrl
from .download_element import DownloadElement
from .error import Error
from .base import JsonModel, integer_column, text_column, enum_column, timestamp_column, register_enum_column,\
    relationship, backref


# ## CLASSES

class Download(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    request_url = text_column(nullable=False)
    status_id = enum_column(foreign_key='download_status.id', nullable=False)
    created = timestamp_column(nullable=False)

    # ## Relationships
    image_urls = relationship(DownloadUrl, uselist=True, cascade='all,delete',
                              backref=backref('download', uselist=False))
    errors = relationship(Error, uselist=True, cascade='all,delete', backref=backref('download', uselist=False))
    elements = relationship(DownloadElement, cascade='all,delete', backref=backref('download', uselist=False))

    # ## Association proxies
    image_url_values = association_proxy('image_urls', 'url')

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

    @property
    def errors_json(self):
        return [dict_filter(error.to_json(), ['module', 'message', 'created']) for error in self.errors]

    # ## Class properties

    @memoized_classproperty
    def repr_attributes(cls):
        mapping = {
            'status_id': ('status', 'status_name'),
        }
        return swap_list_values(super().repr_attributes, mapping)

    @memoized_classproperty
    def json_attributes(cls):
        return cls.repr_attributes + [('image_urls', 'image_url_values'), 'post_ids', 'complete_post_ids',
                                      'duplicate_post_ids', 'illust_id', 'artist_id', ('errors', 'errors_json')]

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
