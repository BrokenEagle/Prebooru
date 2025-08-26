# APP/MODELS/ARCHIVE_POST.PY

# ## PYTHON IMPORTS
import os

# ## EXTERNAL IMPORTS
from flask import has_app_context
from sqlalchemy.util import memoized_property

# ## PACKAGE IMPORTS
from config import MEDIA_DIRECTORY, PREVIEW_DIMENSIONS
from utility.obj import memoized_classproperty
from utility.data import swap_list_values
from utility.file import filename_join, network_path_join

# ## LOCAL IMPORTS
from .. import DB
from .model_enums import PostType
from .error import errors_json
from .notation import notations_json
from .base import JsonModel, integer_column, enum_column, text_column, real_column, boolean_column, md5_column,\
    json_column, timestamp_column, image_server_url, register_enum_column, json_list_proxy


# ## FUNCTIONS

def check_app_context(func):
    def wrapper(*args):
        if not has_app_context():
            return None
        return func(*args)
    return wrapper


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
    frames = json_column(nullable=True)
    tags = json_column(nullable=True)
    notations = json_column(nullable=True)
    errors = json_column(nullable=True)

    # Instance properties

    @property
    def directory(self):
        return os.path.join(MEDIA_DIRECTORY, 'archive', self.md5[0:2], self.md5[2:4])

    @property
    def frame_directory(self):
        return os.path.join(self.directory, self.md5)

    def frame(self, num):
        return os.path.join(self.frame_directory, self._frame_filename(num))

    @check_app_context
    def frame_url(self, num):
        return image_server_url(network_path_join('archive', self._partial_network_path, self._frame_filename(num)),
                                subtype='main')

    @property
    def is_image(self):
        return self.file_ext in ['jpg', 'png', 'gif']

    @property
    def is_ugoira(self):
        return self.frames is not None

    @property
    def is_video(self):
        return self.file_ext in ['mp4']

    @property
    def has_preview(self):
        return self.width > PREVIEW_DIMENSIONS[0] or self.height > PREVIEW_DIMENSIONS[1]

    @property
    @check_app_context
    def file_url(self):
        return image_server_url(self._network_path('archive', self.file_ext), 'main')\
            if not self.is_ugoira else self.frame_url(0)

    @property
    @check_app_context
    def preview_url(self):
        return image_server_url(self._network_path('archive_preview', 'jpg'), 'main')\
            if self.has_preview else self.file_url

    @property
    def file_path(self):
        return os.path.join(self.directory, filename_join(self._partial_file_path, self.file_ext))\
            if not self.is_ugoira else self.frame(0)

    @property
    def preview_path(self):
        return os.path.join(MEDIA_DIRECTORY, 'archive_preview', filename_join(self._partial_file_path, 'jpg'))\
            if self.has_preview else self.file_path

    tags_json = json_list_proxy('tags', str)
    errors_json = errors_json
    notations_json = notations_json

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
        }
        return swap_list_values(cls.repr_attributes, mapping)

    @memoized_classproperty
    def recreate_attributes(cls):
        mapping = {
            'type_id': 'type_name',
        }
        return swap_list_values(super().recreate_attributes, mapping) + ['frames']

    # ## Private

    def _frame_filename(self, num):
        return filename_join(str(num).zfill(6), self.file_ext)

    def _network_path(self, subpath, ext):
        return network_path_join(subpath, filename_join(self._partial_network_path, ext))

    @memoized_property
    def _partial_network_path(self):
        return '%s/%s/%s' % (self.md5[0:2], self.md5[2:4], self.md5)

    @memoized_property
    def _partial_file_path(self):
        return os.path.join(self.md5[0:2], self.md5[2:4], self.md5)


# ## Initialize

def initialize():
    DB.Index(None, ArchivePost.md5, unique=True)
    register_enum_column(ArchivePost, PostType, 'type')
