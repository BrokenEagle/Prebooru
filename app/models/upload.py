# APP/MODELS/UPLOAD.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property

# ## LOCAL IMPORTS
from .. import DB
from ..enum_imports import upload_status
from .illust_url import IllustUrl
from .error import Error
from .base import JsonModel, EpochTimestamp, get_relation_definitions


# ## CLASSES

class Upload(JsonModel):
    # ## Columns
    id = DB.Column(DB.Integer, primary_key=True)
    status, status_id, status_name, status_enum, status_filter, status_col =\
        get_relation_definitions(upload_status, relname='status', relcol='id', colname='status_id',
                                 tblname='upload', nullable=False)
    media_filepath = DB.Column(DB.TEXT, nullable=True)
    sample_filepath = DB.Column(DB.TEXT, nullable=True)
    illust_url_id = DB.Column(DB.Integer, DB.ForeignKey('illust_url.id'), nullable=True)
    created = DB.Column(EpochTimestamp(nullable=False), nullable=False)

    # ## Relationships
    errors = DB.relationship(Error, lazy=True, uselist=True, cascade='all,delete',
                             backref=DB.backref('upload', lazy=True, uselist=False))
    illust_url = DB.relationship(IllustUrl, lazy=True, uselist=False, viewonly=True,
                                 backref=DB.backref('uploads', lazy=True, uselist=True))

    # ## Instance properties

    @property
    def post(self):
        return getattr(self.illust_url, 'post', None)

    @property
    def post_id(self):
        return getattr(self.illust_url, 'post_id', None)

    @property
    def site_id(self):
        return self._source.SITE_ID

    @memoized_property
    def site_illust_id(self):
        if self.illust is not None:
            return self.illust.site_illust_id

    @memoized_property
    def illust(self):
        return self.illust_url.illust if self.illust_url_id is not None else None

    @property
    def illust_id(self):
        return getattr(self.illust, 'id', None)

    @memoized_property
    def artist(self):
        return getattr(self.illust, 'artist', None)

    @property
    def artist_id(self):
        return getattr(self.artist, 'id', None)

    # ## Private

    @memoized_property
    def _source(self):
        return self.illust_url.site.source


# ## INITIALIZATION

def initialize():
    # Access the opposite side of the relationship to force the back reference to be generated
    IllustUrl.uploads.property._configure_started
    Upload.set_relation_properties()
