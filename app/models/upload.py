# APP/MODELS/UPLOAD.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property

# ## PACKAGE IMPORTS
from utility.obj import classproperty, memoized_classproperty
from utility.data import swap_list_values

# ## LOCAL IMPORTS
from .model_enums import UploadStatus
from .illust_url import IllustUrl
from .error import Error
from .base import JsonModel, integer_column, text_column, enum_column, timestamp_column, register_enum_column,\
    relationship, backref


# ## CLASSES

class Upload(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    status_id = enum_column(foreign_key='upload_status.id', nullable=False)
    media_filepath = text_column(nullable=False)
    sample_filepath = text_column(nullable=True)
    illust_url_id = integer_column(foreign_key='illust_url.id', nullable=False)
    created = timestamp_column(nullable=False)

    # ## Relationships
    errors = relationship(Error, uselist=True, cascade='all,delete', backref=backref('upload', uselist=False))
    illust_url = relationship(IllustUrl, uselist=False, viewonly=True, backref=backref('uploads', uselist=True))

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

    # ## Class properties

    @memoized_classproperty
    def repr_attributes(cls):
        mapping = {
            'status_id': ('status', 'status_name'),
        }
        return swap_list_values(super().repr_attributes, mapping)

    @classproperty
    def json_attributes(cls):
        return cls.repr_attributes

    # ## Private

    @memoized_property
    def _source(self):
        return self.illust_url.source


# ## INITIALIZATION

def initialize():
    # Access the opposite side of the relationship to force the back reference to be generated
    IllustUrl.uploads.property._configure_started
    Upload.set_relation_properties()
    register_enum_column(Upload, UploadStatus, 'status')
