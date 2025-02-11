# APP/MODELS/ARCHIVE_POST.PY

# ## PYTHON IMPORTS
import os

# ## EXTERNAL IMPORTS
from sqlalchemy.util import memoized_property

# ## PACKAGE IMPORTS
from config import MEDIA_DIRECTORY, PREVIEW_DIMENSIONS
from utility.obj import memoized_classproperty
from utility.data import swap_list_values

# ## LOCAL IMPORTS
from .. import DB
from .model_enums import PostType
from .error import errors_json
from .notation import notations_json
from .base import JsonModel, integer_column, enum_column, text_column, real_column, boolean_column, md5_column,\
    json_column, timestamp_column, image_server_url, register_enum_column, json_list_proxy


# ## CLASSES

class ArchivePost(JsonModel):
    # #### Columns
    archive_id = integer_column(foreign_key='archive.id', primary_key=True)
    width = integer_column(nullable=False)
    height = integer_column(nullable=False)
    file_ext = text_column(nullable=False)
    md5 = md5_column(nullable=False)
    size = integer_column(nullable=False)
    danbooru_id = integer_column(nullable=True)
    created = timestamp_column(nullable=False)
    type_id = enum_column(foreign_key='post_type.id', nullable=False)
    pixel_md5 = md5_column(nullable=True)
    duration = real_column(nullable=True)
    audio = boolean_column(nullable=True)
    tags = json_column(nullable=True)
    notations = json_column(nullable=True)
    errors = json_column(nullable=True)
    illusts = json_column(nullable=True)

    # Instance properties

    @property
    def is_image(self):
        return self.file_ext in ['jpg', 'png', 'gif']

    @property
    def is_video(self):
        return self.file_ext in ['mp4']

    @property
    def has_preview(self):
        return self.width > PREVIEW_DIMENSIONS[0] or self.height > PREVIEW_DIMENSIONS[1]

    @property
    def file_url(self):
        return image_server_url('archive' + self._partial_network_path + self.file_ext, 'main')

    @property
    def preview_url(self):
        if not self.has_preview:
            return self.file_url
        return image_server_url('archive_preview' + self._partial_network_path + 'jpg', 'main')

    @property
    def file_path(self):
        return os.path.join(MEDIA_DIRECTORY, 'archive', self._partial_file_path + self.file_ext)

    @property
    def preview_path(self):
        if self.has_preview:
            return os.path.join(MEDIA_DIRECTORY, 'archive_preview', self._partial_file_path + 'jpg')
        return None

    tags_json = json_list_proxy('tags', str)
    errors_json = errors_json
    notations_json = notations_json
    illusts_json = json_list_proxy('illusts', str)

    # Class properties

    @memoized_classproperty
    def repr_attributes(cls):
        mapping = {
            'type_id': ('type', 'type_name'),
        }
        return swap_list_values(super().repr_attributes, mapping)

    @memoized_classproperty
    def json_attributes(cls):
        mapping = {
            'tags': ('tags', 'tags_json'),
            'errors': ('errors', 'errors_json'),
            'notations': ('notations', 'notations_json'),
            'illusts': ('illusts', 'illusts_json'),
        }
        return swap_list_values(cls.repr_attributes, mapping)

    @memoized_classproperty
    def recreate_attributes(cls):
        mapping = {
            'type_id': 'type_name',
        }
        return swap_list_values(super().recreate_attributes, mapping)

    # ## Private

    @memoized_property
    def _partial_network_path(self):
        return '/%s/%s/%s.' % (self.md5[0:2], self.md5[2:4], self.md5)

    @memoized_property
    def _partial_file_path(self):
        return os.path.join(self.md5[0:2], self.md5[2:4], self._file_name)

    @memoized_property
    def _file_name(self):
        return '%s.' % (self.md5)


# ## Initialize

def initialize():
    DB.Index(None, ArchivePost.md5, unique=True)
    register_enum_column(ArchivePost, PostType, 'type')
