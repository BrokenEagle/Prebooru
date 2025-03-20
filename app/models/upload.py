# APP/MODELS/UPLOAD.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

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

    # ## Association proxies
    post = association_proxy('illust_url', 'post')
    illust = association_proxy('illust_url', 'illust')

    # ## Instance properties

    @property
    def md5(self):
        return getattr(self.illust_url, 'md5', None)

    @property
    def artist(self):
        return getattr(self.illust, 'artist', None)

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
