# APP/MODELS/ILLUST_URL.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import DB
from ..sites import GetSiteDomain, GetSiteKey
from ..base_model import JsonModel, IntOrNone


# ##GLOBAL VARIABLES


@dataclass
class IllustUrl(JsonModel):
    id: int
    site_id: int
    url: str
    width: IntOrNone
    height: IntOrNone
    order: int
    illust_id: int
    active: bool
    id = DB.Column(DB.Integer, primary_key=True)
    site_id = DB.Column(DB.Integer, nullable=False)
    url = DB.Column(DB.String(255), nullable=False)
    width = DB.Column(DB.Integer, nullable=True)
    height = DB.Column(DB.Integer, nullable=True)
    order = DB.Column(DB.Integer, nullable=False)
    illust_id = DB.Column(DB.Integer, DB.ForeignKey('illust.id'), nullable=False)
    active = DB.Column(DB.Boolean, nullable=False)

    @property
    def full_url(self):
        if not hasattr(self, '__full_url'):
            self.__full_url = self._source.GetMediaUrl(self)
        return self.__full_url

    @property
    def _source(self):
        if not hasattr(self, '__source'):
            from ..sources import SOURCEDICT
            site_key = GetSiteKey(self.site_id)
            self.__source = SOURCEDICT[site_key]
        return self.__source

    @property
    def site_domain(self):
        return GetSiteDomain(self.site_id)

    basic_attributes = ['id', 'site_id', 'url', 'width', 'height', 'order', 'illust_id', 'active']
    relation_attributes = ['illust', 'post']
    searchable_attributes = basic_attributes + relation_attributes
