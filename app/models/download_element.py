# APP/MODELS/DOWNLOAD_ELEMENT.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.ext.associationproxy import association_proxy

# ## LOCAL IMPORTS
from .. import DB
from .model_enums import DownloadElementStatus
from .error import Error
from .base import JsonModel, integer_column, enum_column, md5_column, register_enum_column, relationship, backref


# ## CLASSES

class DownloadElement(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    download_id = integer_column(foreign_key='download.id', nullable=False, index=True)
    illust_url_id = integer_column(foreign_key='illust_url.id', nullable=False)
    md5 = md5_column(nullable=True)
    status_id = enum_column(foreign_key='download_element_status.id', nullable=False)

    # ## Relationships
    errors = relationship(Error, uselist=True, cascade='all,delete', backref=backref('download_element', uselist=False))
    # (MtO) download [Download]
    # (MtO) illust_url [IllustUrl]

    # ## Association proxies
    post = association_proxy('illust_url', 'post')


# ## INITIALIZATION

def initialize():
    from .download import Download
    DB.Index(None, DownloadElement.md5, unique=False, sqlite_where=DownloadElement.md5.is_not(None))
    # Access the opposite side of the relationship to force the back reference to be generated
    Download.elements.property._configure_started
    DownloadElement.set_relation_properties()
    register_enum_column(DownloadElement, DownloadElementStatus, 'status')
