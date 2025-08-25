# APP/MODELS/ILLUST_URL.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from utility.obj import memoized_classproperty
from utility.data import list_difference, swap_list_values

# ## LOCAL IMPORTS
from ..logical.sites import domain_by_site_name
from .model_enums import SiteDescriptor
from .ugoira import Ugoira, ugoira_creator
from .post import Post
from .download_element import DownloadElement
from .subscription_element import SubscriptionElement
from .archive_post import ArchivePost
from .base import JsonModel, integer_column, text_column, enum_column, boolean_column, md5_column,\
    register_enum_column, relationship, backref


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
    md5 = md5_column(nullable=True)
    ugoira_id = integer_column(foreign_key='ugoira.id', nullable=True)

    # ## Relationships
    ugoira = relationship(Ugoira, uselist=False)
    download_elements = relationship(DownloadElement, uselist=True, cascade="all, delete",
                                     backref=backref('illust_url', uselist=False))
    subscription_element = relationship(SubscriptionElement, uselist=False, cascade="all, delete",
                                        backref=backref('illust_url', uselist=False))
    post = relationship(Post, primaryjoin=(md5 == Post.md5), foreign_keys=md5, passive_deletes='all',
                        remote_side=Post.md5, uselist=False, overlaps="illust_urls,archive_post",
                        backref=backref('illust_urls', uselist=True, overlaps="illust_urls,archive_post",
                                        passive_deletes='all'))
    archive_post = relationship(ArchivePost, primaryjoin=(md5 == ArchivePost.md5), foreign_keys=md5,
                                remote_side=ArchivePost.md5, uselist=False, overlaps="illust_urls,post",
                                backref=backref('illust_urls', uselist=True, overlaps="illust_urls,post"))
    # (MtO) illust [Illust]
    # (MtO) post [Post]
    # (OtO) uploads [Upload]

    # ## Association proxies
    frames = association_proxy('ugoira', 'frames', creator=ugoira_creator)

    # ## Instance functions

    def frame(self, num):
        return self.source.get_frame_url(self, num)

    @memoized_property
    def source(self):
        from ..logical.sources import source_by_site_name
        return source_by_site_name(self.site.name)

    @memoized_property
    def type(self):
        if self.source.video_url_mapper(self):
            return 'video'
        elif self.source.image_url_mapper(self):
            return 'image'
        elif self.source.ugoira_url_mapper(self):
            return 'ugoira'
        else:
            return 'unknown'

    @memoized_property
    def preview_url(self):
        if self.type in ['image', 'ugoira']:
            return self.source.get_preview_url(self)
        elif self.type == 'video':
            return self.full_sample_url
        return None

    @memoized_property
    def has_alternate(self):
        return self.source.has_alternate(self)

    @property
    def full_url(self):
        return self.source.get_media_url(self)

    @property
    def original_url(self):
        return self.source.get_full_url(self)

    @property
    def alternate_url(self):
        return self.source.get_alternate_url(self)

    @property
    def url_extension(self):
        return self.source.get_media_extension(self.full_url)

    @property
    @check_video
    def full_sample_url(self):
        return self.source.get_sample_url(self)

    @property
    @check_video
    def original_sample_url(self):
        return self.source.get_sample_url(self, True)

    @property
    @check_video
    def alternate_sample_url(self):
        return self.source.get_sample_url(self, False)

    @property
    def site_domain(self):
        return domain_by_site_name(self.site_name)

    @property
    def sample_site_domain(self):
        return domain_by_site_name(self.sample_site_name)

    # ## Class functions

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
            'ugoira_id': 'frames',
        }
        attributes = list_difference(super().json_attributes, ['site_id', 'sample_site_id'])
        return swap_list_values(attributes, mapping)


# ## INITIALIZATION

def initialize():
    from .illust import Illust
    # Access the opposite side of the relationship to force the back reference to be generated
    Illust.urls.property._configure_started
    IllustUrl.set_relation_properties()
    register_enum_column(IllustUrl, SiteDescriptor, 'site')
    register_enum_column(IllustUrl, SiteDescriptor, 'sample_site')
