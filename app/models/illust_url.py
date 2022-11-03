# APP/MODELS/ILLUST_URL.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property

# ## PACKAGE IMPORTS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..logical.sites import Site
from .upload_element import UploadElement
from .subscription_element import SubscriptionElement
from .base import JsonModel, IntEnum


# ## CLASSES

class IllustUrl(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    site_id = DB.Column(IntEnum(Site), nullable=False)
    url = DB.Column(DB.String(255), nullable=False)
    sample_id = DB.Column(DB.Integer, nullable=True)
    sample = DB.Column(DB.String(255), nullable=True)
    width = DB.Column(DB.Integer, nullable=False)
    height = DB.Column(DB.Integer, nullable=False)
    order = DB.Column(DB.Integer, nullable=False)
    illust_id = DB.Column(DB.Integer, DB.ForeignKey('illust.id'), nullable=False, index=True)
    active = DB.Column(DB.Boolean, nullable=False)

    # ## Relationships
    upload_elements = DB.relationship(UploadElement, lazy=True, uselist=True,
                                      backref=DB.backref('illust_url', lazy=True, uselist=False),
                                      cascade="all, delete")
    subscription_element = DB.relationship(SubscriptionElement, lazy=True, uselist=False,
                                           backref=DB.backref('illust_url', lazy=True, uselist=False),
                                           cascade="all, delete")

    # ## Property methods

    @memoized_property
    def type(self):
        if self.site_id.source.video_url_mapper(self):
            return 'video'
        elif self.site_id.source.image_url_mapper(self):
            return 'image'
        else:
            return 'unknown'

    @memoized_property
    def preview_url(self):
        if self.type == 'image':
            return self.site_id.source.get_preview_url(self)
        elif self.type == 'video':
            return self.sample_url

    @memoized_property
    def full_url(self):
        return self.site_id.source.get_media_url(self)

    @memoized_property
    def sample_url(self):
        return self.site_id.source.get_sample_url(self)

    @property
    def site_domain(self):
        return self.site_id.domain

    # ## Class properties

    site_id_enum = Site

    @classproperty(cached=True)
    def json_attributes(cls):
        return super().json_attributes + ['full_url', 'site_domain']


# ## INITIALIZATION

def initialize():
    from .upload import Upload
    from .illust import Illust
    IllustUrl.uploads = DB.relationship(Upload, backref=DB.backref('illust_url', lazy=True), lazy=True)
    # Access the opposite side of the relationship to force the back reference to be generated
    Illust.urls.property._configure_started
    IllustUrl.set_relation_properties()
