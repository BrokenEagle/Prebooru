# APP/MODELS/ARCHIVE.PY

# ## PYTHON IMPORTS
import os

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from config import MEDIA_DIRECTORY, PREVIEW_DIMENSIONS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..enum_imports import archive_type
from .media_asset import MediaAsset
from .base import JsonModel, EpochTimestamp, image_server_url, get_relation_definitions


# ## FUNCTIONS

def check_type(func):
    def wrapper(*args):
        if not args[0].is_post_type:
            return None
        return func(*args)
    return wrapper


# ## CLASSES

class Archive(JsonModel):
    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    type, type_id, type_name, type_enum, type_filter, type_col =\
        get_relation_definitions(archive_type, relname='type', relcol='id', colname='type_id',
                                 tblname='archive', nullable=False)
    key = DB.Column(DB.String(255), nullable=False)
    data = DB.Column(DB.JSON, nullable=False)
    expires = DB.Column(EpochTimestamp(nullable=True), nullable=True)
    media_asset_id = DB.Column(DB.INTEGER, DB.ForeignKey('media_asset.id'), nullable=True)

    # ## Relationships
    media = DB.relationship(MediaAsset, lazy=True, uselist=False,
                            backref=DB.backref('archive', lazy=True, uselist=False))

    # ## Association proxies
    width = association_proxy('media', 'width')
    height = association_proxy('media', 'height')
    size = association_proxy('media', 'size')
    md5 = association_proxy('media', 'md5')
    file_ext = association_proxy('media', 'file_ext')
    pixel_md5 = association_proxy('media', 'pixel_md5')
    duration = association_proxy('media', 'duration')
    audio = association_proxy('media', 'audio')
    location = association_proxy('media', 'location')
    file_path = association_proxy('media', 'original_file_path')
    file_url = association_proxy('media', 'original_file_url')

    @property
    def is_post_type(self):
        return self.type.name == 'post'

    @property
    @check_type
    def has_preview(self):
        return self.width > PREVIEW_DIMENSIONS[0] or self.height > PREVIEW_DIMENSIONS[1] or self.media.is_video

    @property
    @check_type
    def file_url(self):
        return self.media.original_file_url

    @property
    @check_type
    def preview_url(self):
        if not self.has_preview:
            return self.file_url
        return self.media.image_preview_url

    @property
    @check_type
    def file_path(self):
        return self.media.original_file_path

    @property
    @check_type
    def preview_path(self):
        if self.has_preview:
            return self.media.image_preview_path

    # ## Class properties

    @classproperty(cached=True)
    def searchable_attributes(cls):
        return [x for x in super().searchable_attributes if x not in ['data']]

    # ###### Private

    @memoized_property
    def _partial_network_path(self):
        return '/%s/%s/%s.' % (self.key[0:2], self.key[2:4], self.key)

    @memoized_property
    def _partial_file_path(self):
        return os.path.join(self.key[0:2], self.key[2:4], self._file_name)

    @memoized_property
    def _file_name(self):
        return '%s.' % (self.key)

    __table_args__ = (
        DB.UniqueConstraint('key', 'type_id'),
    )
