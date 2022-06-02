# APP/MODELS/ILLUST_URL.PY

# ## LOCAL IMPORTS
from .. import DB
from ..logical.sites import get_site_domain, get_site_key
from .subscription_pool_element import SubscriptionPoolElement
from .base import JsonModel, classproperty


# ## CLASSES

class IllustUrl(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    site_id = DB.Column(DB.Integer, nullable=False)
    url = DB.Column(DB.String(255), nullable=False)
    width = DB.Column(DB.Integer, nullable=True)
    height = DB.Column(DB.Integer, nullable=True)
    order = DB.Column(DB.Integer, nullable=False)
    illust_id = DB.Column(DB.Integer, DB.ForeignKey('illust.id'), nullable=False)
    active = DB.Column(DB.Boolean, nullable=False)

    # ## Relationships
    subscription_pool_element = DB.relationship(SubscriptionPoolElement, lazy=True, uselist=False,
                                                backref=DB.backref('illust_url', lazy=True, uselist=False),
                                                cascade="all, delete")

    # ## Property methods

    @property
    def type(self):
        if self._source.video_url_mapper(self):
            return 'video'
        elif self._source.image_url_mapper(self):
            return 'image'
        else:
            return 'unknown'

    @property
    def full_url(self):
        if not hasattr(self, '__full_url'):
            self.__full_url = self._source.get_media_url(self)
        return self.__full_url

    @property
    def _source(self):
        if not hasattr(self, '__source'):
            from ..logical.sources import SOURCEDICT
            site_key = get_site_key(self.site_id)
            self.__source = SOURCEDICT[site_key]
        return self.__source

    @property
    def site_domain(self):
        return get_site_domain(self.site_id)

    # ## Class properties

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
