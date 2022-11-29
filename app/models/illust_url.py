# APP/MODELS/ILLUST_URL.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property

# ## PACKAGE IMPORTS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..logical.enums import SiteDescriptorEnum
from .upload_element import UploadElement
from .subscription_element import SubscriptionElement
from .base import JsonModel, IntEnum


# ## CLASSES

class IllustUrl(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    site_id = DB.Column(IntEnum(SiteDescriptorEnum), nullable=False)
    url = DB.Column(DB.String(255), nullable=False)
    sample_site_id = DB.Column(IntEnum(SiteDescriptorEnum, nullable=True), nullable=True)
    sample_url = DB.Column(DB.String(255), nullable=True)
    width = DB.Column(DB.Integer, nullable=False)
    height = DB.Column(DB.Integer, nullable=False)
    order = DB.Column(DB.Integer, nullable=False)
    illust_id = DB.Column(DB.Integer, DB.ForeignKey('illust.id'), nullable=False, index=True)
    active = DB.Column(DB.Boolean, nullable=False)

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

    # ## Class properties

    site_enum = SiteDescriptorEnum
    sample_site_enum = SiteDescriptorEnum

    @classproperty(cached=True)
    def json_attributes(cls):
        return super().json_attributes + ['full_url', 'site_domain']


# ## INITIALIZATION

def initialize():
    from .illust import Illust
    # Access the opposite side of the relationship to force the back reference to be generated
    Illust.urls.property._configure_started
    IllustUrl.set_relation_properties()
