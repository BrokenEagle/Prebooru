# APP/MODELS/ILLUST_URL.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property

# ## PACKAGE IMPORTS
from utility.obj import memoized_classproperty
from utility.data import list_difference, swap_list_values

# ## LOCAL IMPORTS
from .. import DB
from ..logical.sites import domain_by_site_name
from .model_enums import SiteDescriptor
from .download_element import DownloadElement
from .subscription_element import SubscriptionElement
from .base import JsonModel, integer_column, text_column, enum_column, boolean_column, register_enum_column,\
    relationship, backref


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
    id = integer_column(primary_key=True)
    site_id = enum_column(foreign_key='site_descriptor.id', nullable=False)
    url = text_column(nullable=False)
    sample_site_id = enum_column(foreign_key='site_descriptor.id', nullable=True)
    sample_url = text_column(nullable=True)
    width = integer_column(nullable=False)
    height = integer_column(nullable=False)
    order = integer_column(nullable=False)
    illust_id = integer_column(foreign_key='illust.id', nullable=False, index=True)
    active = boolean_column(nullable=False)
    post_id = integer_column(foreign_key='post.id', nullable=True)

    # ## Relationships
    download_elements = relationship(DownloadElement, uselist=True, cascade="all, delete",
                                     backref=backref('illust_url', uselist=False))
    subscription_element = relationship(SubscriptionElement, uselist=False, cascade="all, delete",
                                        backref=backref('illust_url', uselist=False))
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
    def md5(self):
        return self.post.md5 if self.post_id is not None else None

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

    # ## Class properties

    @memoized_classproperty
    def repr_attributes(cls):
        mapping = {
            'site_id': ('site', 'site_name'),
            'sample_site_id': ('sample_site', 'sample_site_name'),
        }
        return swap_list_values(super().repr_attributes, mapping)

    @memoized_classproperty
    def json_attributes(cls):
        mapping = {
            'url': ('url', 'full_url'),
            'sample_url': ('sample_url', 'full_sample_url'),
        }
        attributes = list_difference(super().json_attributes, ['site_id', 'sample_site_id'])
        return swap_list_values(attributes, mapping)


# ## INITIALIZATION

def initialize():
    from .illust import Illust
    DB.Index(None, IllustUrl.post_id, unique=False, sqlite_where=IllustUrl.post_id.is_not(None))
    # Access the opposite side of the relationship to force the back reference to be generated
    Illust.urls.property._configure_started
    IllustUrl.set_relation_properties()
    register_enum_column(IllustUrl, SiteDescriptor, 'site')
    register_enum_column(IllustUrl, SiteDescriptor, 'sample_site')
