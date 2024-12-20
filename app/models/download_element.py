# APP/MODELS/DOWNLOAD_ELEMENT.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.ext.associationproxy import association_proxy

# ## LOCAL IMPORTS
from .. import DB
from ..enum_imports import download_element_status
from .error import Error
from .base import JsonModel, BlobMD5, get_relation_definitions


# ## CLASSES

class DownloadElement(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    download_id = DB.Column(DB.Integer, DB.ForeignKey('download.id'), nullable=False, index=True)
    illust_url_id = DB.Column(DB.Integer, DB.ForeignKey('illust_url.id'), nullable=False)
    md5 = DB.Column(BlobMD5(nullable=True), nullable=True)
    status, status_id, status_name, status_enum, status_filter, status_col =\
        get_relation_definitions(download_element_status, relname='status', relcol='id', colname='status_id',
                                 tblname='download_element', nullable=False)

    # ## Relationships
    errors = DB.relationship(Error, lazy=True, uselist=True, cascade='all,delete',
                             backref=DB.backref('download_element', lazy=True, uselist=False))
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
