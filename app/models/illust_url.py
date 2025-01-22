# APP/MODELS/ILLUST_URL.PY

# ## PYTHON IMPORTS
import base64
import hashlib

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property

# ## PACKAGE IMPORTS
from utility.obj import classproperty
from utility.data import list_difference

# ## LOCAL IMPORTS
from .. import DB
from ..logical.sites import domain_by_site_name
from .model_enums import SiteDescriptor
from .download_element import DownloadElement
from .subscription_element import SubscriptionElement
from .base import JsonModel, IntEnum, register_enum_column


# ## FUNCTIONS

def check_video(func):
    def wrapper(*args):
        if args[0].type != 'video':
            return None
        return func(*args)
    return wrapper


# ## CLASSES

class IllustUrl(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    site_id = DB.Column(IntEnum, DB.ForeignKey('site_descriptor.id'), nullable=False)
    url = DB.Column(DB.TEXT, nullable=False)
    sample_site_id = DB.Column(IntEnum, DB.ForeignKey('site_descriptor.id'), nullable=True)
    sample_url = DB.Column(DB.TEXT, nullable=True)
    width = DB.Column(DB.Integer, nullable=False)
    height = DB.Column(DB.Integer, nullable=False)
    order = DB.Column(DB.Integer, nullable=False)
    illust_id = DB.Column(DB.Integer, DB.ForeignKey('illust.id'), nullable=False, index=True)
    active = DB.Column(DB.Boolean, nullable=False)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=True)

    # ## Relationships
    download_elements = DB.relationship(DownloadElement, lazy=True, uselist=True, cascade="all, delete",
                                        backref=DB.backref('illust_url', lazy=True, uselist=False))
    subscription_element = DB.relationship(SubscriptionElement, lazy=True, uselist=False, cascade="all, delete",
                                           backref=DB.backref('illust_url', lazy=True, uselist=False))
    # (MtO) illust [Illust]
    # (MtO) post [Post]
    # (OtO) upload [Upload]

    # ## Instance properties

    @property
    def source(self):
        from ..logical.sources import source_by_site_name
        return source_by_site_name(self.site.name)

    @memoized_property
    def type(self):
        if self.source.video_url_mapper(self):
            return 'video'
        elif self.source.image_url_mapper(self):
            return 'image'
        else:
            return 'unknown'

    @memoized_property
    def preview_url(self):
        if self.type == 'image':
            return self.source.get_preview_url(self)
        elif self.type == 'video':
            return self.full_sample_url

    @memoized_property
    def full_url(self):
        return self.source.get_media_url(self)

    @memoized_property
    def original_url(self):
        return self.source.get_full_url(self)

    @memoized_property
    def alternate_url(self):
        return self.source.get_alternate_url(self)

    @memoized_property
    def url_extension(self):
        return self.source.get_media_extension(self.full_url)

    @memoized_property
    @check_video
    def full_sample_url(self):
        return self.source.get_sample_url(self)

    @memoized_property
    @check_video
    def original_sample_url(self):
        return self.source.get_sample_url(self, True)

    @memoized_property
    @check_video
    def alternate_sample_url(self):
        return self.source.get_sample_url(self, False)

    @memoized_property
    @check_video
    def sample_extension(self):
        return self.source.get_media_extension(self.full_sample_url)

    @property
    def site_domain(self):
        return domain_by_site_name(self.site_name)

    @property
    def sample_site_domain(self):
        return domain_by_site_name(self.sample_site_name)

    @property
    def key(self):
        return self.full_url

    @property
    def hash_key(self):
        digest = hashlib.md5(self.full_url.encode('utf')).digest()[:3]
        return base64.b64encode(digest).decode()

    @property
    def link_key(self):
        return {'md5': self.post.md5, 'key': self.hash_key}

    # ## Class properties

    @classmethod
    def find_by_key(cls, full_url):
        from ..logical.sites import site_name_by_url
        from ..logical.sources import source_by_site_name
        site_name = site_name_by_url(full_url)
        source = source_by_site_name(site_name)
        partial = source.partial_media_url(full_url)
        return cls.query.filter(cls.site_value == site_name, cls.url == partial).one_or_none()

    @classmethod
    def loads(cls, data, *args):
        from ..logical.sites import site_name_by_url
        from ..logical.sources import source_by_site_name
        if 'url' in data and data['url'].startswith('http'):
            site_name = site_name_by_url(data['url'])
            source = source_by_site_name(site_name)
            data['site_id'] = SiteDescriptor.to_id(site_name)
            data['url'] = source.partial_media_url(data['url'])
        if 'sample' in data and data['sample'] is not None and data['sample'].startswith('http'):
            sample_site_name = site_name_by_url(data['sample'])
            sample_source = source_by_site_name(sample_site_name)
            data['sample_site_id'] = SiteDescriptor.to_id(sample_site_name)
            data['sample_url'] = sample_source.partial_media_url(data['sample'])
        return super().loads(data)

    archive_excludes = {'url', 'site', 'site_id', 'sample', 'sample_url', 'sample_site_id'}
    archive_includes = {('url', 'full_url'), ('sample', 'full_sample_url'), ('key', 'hash_key')}

    @classproperty(cached=True)
    def repr_attributes(cls):
        return list_difference(super().json_attributes, ['site_id', 'sample_site_id'])\
            + ['site_name', 'sample_site_name']

    @classproperty(cached=True)
    def json_attributes(cls):
        return cls.repr_attributes + ['full_url', 'full_sample_url', 'site_domain']


# ## INITIALIZATION

def initialize():
    from .illust import Illust
    DB.Index(None, IllustUrl.post_id, unique=False, sqlite_where=IllustUrl.post_id.is_not(None))
    # Access the opposite side of the relationship to force the back reference to be generated
    Illust.urls.property._configure_started
    IllustUrl.set_relation_properties()
    register_enum_column(IllustUrl, SiteDescriptor, 'site')
    register_enum_column(IllustUrl, SiteDescriptor, 'sample_site')
