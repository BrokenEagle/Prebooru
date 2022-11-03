# APP/MODELS/ARCHIVE.PY

# ## PYTHON IMPORTS
import os
import enum

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property

# ## PACKAGE IMPORTS
from config import MEDIA_DIRECTORY, PREVIEW_DIMENSIONS
from utility.obj import AttrEnum, classproperty

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel, IntEnum, EpochTimestamp, image_server_url


# ## CLASSES

class ArchiveType(AttrEnum):
    post = enum.auto()
    illust = enum.auto()
    artist = enum.auto()
    booru = enum.auto()


class Archive(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    type = DB.Column(IntEnum(ArchiveType), nullable=False)
    key = DB.Column(DB.String(255), nullable=False)
    data = DB.Column(DB.JSON, nullable=False)
    expires = DB.Column(EpochTimestamp(nullable=True), nullable=True)

    @property
    def has_preview(self):
        if self.type != ArchiveType.post:
            return
        return self.data['body']['width'] > PREVIEW_DIMENSIONS[0] or\
            self.data['body']['height'] > PREVIEW_DIMENSIONS[1]

    @property
    def file_url(self):
        if self.type != ArchiveType.post:
            return
        return image_server_url('archive' + self._partial_network_path + self.data['body']['file_ext'], 'main')

    @property
    def preview_url(self):
        if self.type != ArchiveType.post:
            return
        if not self.has_preview:
            return self.file_url
        return image_server_url('archive_preview' + self._partial_network_path + 'jpg', 'main')

    @property
    def file_path(self):
        if self.type != ArchiveType.post:
            return
        return os.path.join(MEDIA_DIRECTORY, 'archive', self._partial_file_path + self.data['body']['file_ext'])

    @property
    def preview_path(self):
        if self.type != ArchiveType.post or not self.has_preview:
            return
        return os.path.join(MEDIA_DIRECTORY, 'archive_preview', self._partial_file_path + 'jpg')

    # ## Class properties

    type_enum = ArchiveType

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
        DB.Index(None, 'type', 'key', unique=True),
    )
