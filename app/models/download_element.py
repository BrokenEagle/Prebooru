# APP/MODELS/DOWNLOAD_ELEMENT.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from utility.obj import classproperty, memoized_classproperty
from utility.data import swap_list_values

# ## LOCAL IMPORTS
from .model_enums import DownloadElementStatus
from .error import Error
from .base import JsonModel, integer_column, enum_column, register_enum_column, relationship, backref


# ## CLASSES

class DownloadElement(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    download_id = integer_column(foreign_key='download.id', nullable=False, index=True)
    illust_url_id = integer_column(foreign_key='illust_url.id', nullable=False)
    status_id = enum_column(foreign_key='download_element_status.id', nullable=False)

    # ## Relationships
    errors = relationship(Error, uselist=True, cascade='all,delete', backref=backref('download_element', uselist=False))
    # (MtO) download [Download]
    # (MtO) illust_url [IllustUrl]

    # ## Association proxies
    post = association_proxy('illust_url', 'post')

    # ## Instance properties

    @property
    def md5(self):
        return getattr(self.illust_url, 'md5', None)

    @memoized_classproperty
    def repr_attributes(cls):
        mapping = {
            'status_id': ('status', 'status_name'),
        }
        return swap_list_values(super().repr_attributes, mapping)

    @classproperty
    def json_attributes(cls):
        return cls.repr_attributes


# ## INITIALIZATION

def initialize():
    from .download import Download
    # Access the opposite side of the relationship to force the back reference to be generated
    Download.elements.property._configure_started
    DownloadElement.set_relation_properties()
    register_enum_column(DownloadElement, DownloadElementStatus, 'status')
