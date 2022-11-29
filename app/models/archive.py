# APP/MODELS/ARCHIVE.PY

# ## PYTHON IMPORTS
import os

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property

# ## PACKAGE IMPORTS
from config import MEDIA_DIRECTORY, PREVIEW_DIMENSIONS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..logical.enums import ArchiveTypeEnum
from .base import JsonModel, IntEnum, EpochTimestamp, image_server_url


# ## CLASSES

class Archive(JsonModel):
    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    type_id = DB.Column(IntEnum(ArchiveTypeEnum), nullable=False)
    key = DB.Column(DB.String(255), nullable=False)
    data = DB.Column(DB.JSON, nullable=False)
    expires = DB.Column(EpochTimestamp(nullable=True), nullable=True)

    @property
    def is_post_type(self):
        return self.type_id.name == 'post'

    @property
    def has_preview(self):
        if not self.is_post_type:
            return
        return self.data['body']['width'] > PREVIEW_DIMENSIONS[0] or\
            self.data['body']['height'] > PREVIEW_DIMENSIONS[1]

    @property
    def file_url(self):
        if not self.is_post_type:
            return
        return image_server_url('archive' + self._partial_network_path + self.data['body']['file_ext'], 'main')

    @property
    def preview_url(self):
        if not self.is_post_type:
            return
        if not self.has_preview:
            return self.file_url
        return image_server_url('archive_preview' + self._partial_network_path + 'jpg', 'main')

    @property
    def file_path(self):
        if not self.is_post_type:
            return
        return os.path.join(MEDIA_DIRECTORY, 'archive', self._partial_file_path + self.data['body']['file_ext'])

    @property
    def preview_path(self):
        if not self.is_post_type or not self.has_preview:
            return
        return os.path.join(MEDIA_DIRECTORY, 'archive_preview', self._partial_file_path + 'jpg')

    # ## Class properties

    type_enum = ArchiveTypeEnum

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
        DB.Index(None, 'type_id', 'key', unique=True),
    )
