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


# ## FUNCTIONS

def populate_illust_urls(func):
    def wrapper(*args):
        if not hasattr(args[0], '_illust_urls'):
            args[0]._populate_illust_urls()
        return func(*args)
    return wrapper


def populate_posts(func):
    def wrapper(*args):
        if not hasattr(args[0], '_posts'):
            args[0]._populate_posts()
        return func(*args)
    return wrapper


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
    def selectin_illust_urls(self):
        return [element.illust_url for element in self.elements]

    @memoized_property
    def selectin_posts(self):
        return [illust_url.post for illust_url in self.selectin_illust_urls if illust_url.post is not None]

    @property
    @populate_illust_urls
    def illust_urls(self):
        return self._illust_urls

    @property
    @populate_illust_urls
    def complete_illust_urls(self):
        return self._complete_illust_urls

    @property
    @populate_illust_urls
    def duplicate_illust_urls(self):
        return self._duplicate_illust_urls

    @property
    @populate_posts
    def posts(self):
        return self._posts

    @property
    @populate_posts
    def complete_posts(self):
        return self._complete_posts

    @property
    @populate_posts
    def duplicate_posts(self):
        return self._duplicate_posts

    @property
    def post_ids(self):
        return [post.id for post in self.posts]

    @property
    def complete_post_ids(self):
        return [post.id for post in self.complete_posts]

    @property
    def duplicate_post_ids(self):
        return [post.id for post in self.duplicate_posts]

    @memoized_property
    def illust(self):
        return next((illust_url.illust for illust_url in self.illust_urls), None)

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

    def _populate_illust_urls(self):
        if len(self.elements):
            selectinload_batch_primary(self.elements, 'illust_url')
        self._illust_urls = [element.illust_url for element in self.elements]
        self._complete_illust_urls = [element.illust_url for element in self.elements
                                      if element.status_name == 'complete']
        self._duplicate_illust_urls = [element.illust_url for element in self.elements
                                       if element.status_name == 'duplicate']

    def _populate_posts(self):
        if len(self.illust_urls):
            selectinload_batch_primary(self.illust_urls, 'post')
        self._posts = [illust_url.post for illust_url in self.illust_urls
                       if illust_url.post is not None]
        self._complete_posts = [illust_url.post for illust_url in self.complete_illust_urls
                                if illust_url.post is not None]
        self._duplicate_posts = [illust_url.post for illust_url in self.duplicate_illust_urls
                                 if illust_url.post is not None]


# ## Initialize

def initialize():
    register_enum_column(Download, DownloadStatus, 'status')
