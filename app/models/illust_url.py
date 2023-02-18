# APP/MODELS/ILLUST_URL.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property

# ## PACKAGE IMPORTS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..enum_imports import site_descriptor
from .upload_element import UploadElement
from .subscription_element import SubscriptionElement
from .base import JsonModel, get_relation_definitions


# ## CLASSES

class IllustUrl(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    site, site_id, site_name, site_enum, site_filter, site_col =\
        get_relation_definitions(site_descriptor, relname='site', relcol='id', colname='site_id',
                                 tblname='illust_url', nullable=False)
    url = DB.Column(DB.TEXT, nullable=False)
    sample_site, sample_site_id, sample_site_name, sample_site_enum, sample_site_filter, sample_site_col =\
        get_relation_definitions(site_descriptor, relname='sample_site', relcol='id', colname='sample_site_id',
                                 tblname='illust_url', nullable=True)
    sample_url = DB.Column(DB.TEXT, nullable=True)
    width = DB.Column(DB.Integer, nullable=False)
    height = DB.Column(DB.Integer, nullable=False)
    order = DB.Column(DB.Integer, nullable=False)
    illust_id = DB.Column(DB.Integer, DB.ForeignKey('illust.id'), nullable=False, index=True)
    active = DB.Column(DB.Boolean, nullable=False)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=True)

    # ## Relationships
    upload_elements = DB.relationship(UploadElement, lazy=True, uselist=True, cascade="all, delete",
                                      backref=DB.backref('illust_url', lazy=True, uselist=False))
    subscription_element = DB.relationship(SubscriptionElement, lazy=True, uselist=False, cascade="all, delete",
                                           backref=DB.backref('illust_url', lazy=True, uselist=False))
    # (MtO) illust [Illust]
    # (MtO) post [Post]
    # (OtO) upload [Upload]

    # ## Instance properties

    @memoized_property
    def type(self):
        if self.site.source.video_url_mapper(self):
            return 'video'
        elif self.site.source.image_url_mapper(self):
            return 'image'
        else:
            return 'unknown'

    @memoized_property
    def preview_url(self):
        if self.type == 'image':
            return self.site.source.get_preview_url(self)
        elif self.type == 'video':
            return self.full_sample_url

    @memoized_property
    def full_url(self):
        return self.site.source.get_media_url(self)

    @memoized_property
    def full_sample_url(self):
        return self.site.source.get_sample_url(self)

    @property
    def site_domain(self):
        return self.site.domain

    def archive_dict(self):
        data = {
            'url': self.full_url,
            'width': self.width,
            'height': self.height,
            'order': self.order,
            'active': self.active,
        }
        if self.type == 'video':
            data['sample'] = self.full_sample_url
        return data

    # ## Class properties

    @classproperty(cached=True)
    def json_attributes(cls):
        return super().json_attributes + ['full_url', 'site_domain']


# ## INITIALIZATION

def initialize():
    from .illust import Illust
    DB.Index(None, IllustUrl.post_id, unique=False, sqlite_where=IllustUrl.post_id.is_not(None))
    # Access the opposite side of the relationship to force the back reference to be generated
    Illust.urls.property._configure_started
    IllustUrl.set_relation_properties()
