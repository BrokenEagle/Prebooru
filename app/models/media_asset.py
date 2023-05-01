# APP/MODELS/MEDIA_ASSET.PY

# ## PYTHON IMPORTS
import os

# ## EXTERNAL IMPORTS
from flask import url_for, has_app_context
from sqlalchemy.util import memoized_property

# ## PACKAGE IMPORTS
from config import IMAGE_PORT, MEDIA_DIRECTORY, ALTERNATE_MEDIA_DIRECTORY, HAS_EXTERNAL_IMAGE_SERVER
from utility.file import path_join

# ## LOCAL IMPORTS
from .. import DB, SERVER_INFO
from ..enum_imports import media_asset_location
from .base import JsonModel, BlobMD5, get_relation_definitions


# #### GLOBAL VARIABLES

ORIGINAL_FILE_PATHS = {
    media_asset_location.primary.id: path_join(MEDIA_DIRECTORY, 'data'),
    media_asset_location.alternate.id: path_join(ALTERNATE_MEDIA_DIRECTORY, 'data'),
    media_asset_location.archive.id: path_join(MEDIA_DIRECTORY, 'archive'),
    media_asset_location.cache.id: path_join(MEDIA_DIRECTORY, 'cache'),
}
IMAGE_SAMPLE_FILE_PATHS = {
    media_asset_location.primary.id: path_join(MEDIA_DIRECTORY, 'sample'),
    media_asset_location.alternate.id: path_join(ALTERNATE_MEDIA_DIRECTORY, 'sample'),
}
IMAGE_PREVIEW_FILE_PATHS = {
    media_asset_location.primary.id: path_join(MEDIA_DIRECTORY, 'preview'),
    media_asset_location.alternate.id: path_join(ALTERNATE_MEDIA_DIRECTORY, 'preview'),
    media_asset_location.archive.id: path_join(MEDIA_DIRECTORY, 'archive_preview'),
}
VIDEO_SAMPLE_FILE_PATHS = {
    media_asset_location.primary.id: path_join(MEDIA_DIRECTORY, 'video_sample'),
    media_asset_location.alternate.id: path_join(ALTERNATE_MEDIA_DIRECTORY, 'video_sample'),
}
VIDEO_PREVIEW_FILE_PATHS = {
    media_asset_location.primary.id: path_join(MEDIA_DIRECTORY, 'video_preview'),
    media_asset_location.alternate.id: path_join(ALTERNATE_MEDIA_DIRECTORY, 'video_preview'),
}

IMAGE_SAMPLE_FILE_EXTS = {
    media_asset_location.primary.id: 'jpg',
    media_asset_location.alternate.id: 'jpg',
}
IMAGE_PREVIEW_FILE_EXTS = {
    media_asset_location.primary.id: 'jpg',
    media_asset_location.alternate.id: 'jpg',
    media_asset_location.archive.id: 'jpg',
}
VIDEO_SAMPLE_FILE_EXTS = {
    media_asset_location.primary.id: 'webm',
    media_asset_location.alternate.id: 'webm',
}
VIDEO_PREVIEW_FILE_EXTS = {
    media_asset_location.primary.id: 'webp',
    media_asset_location.alternate.id: 'webp',
    media_asset_location.archive.id: 'webp',
}

SUBURL_PATHS = {
    media_asset_location.primary.id: 'main',
    media_asset_location.alternate.id: 'alternate',
    media_asset_location.archive.id: 'main',
    media_asset_location.cache.id: 'main',
}
ORIGINAL_SUBDIR_PATHS = {
    media_asset_location.primary.id: 'data',
    media_asset_location.alternate.id: 'data',
    media_asset_location.archive.id: 'archive',
    media_asset_location.cache.id: 'cache',
}
SAMPLE_SUBDIR_PATHS = {
    media_asset_location.primary.id: 'sample',
    media_asset_location.alternate.id: 'sample',
}
PREVIEW_SUBDIR_PATHS = {
    media_asset_location.primary.id: 'preview',
    media_asset_location.alternate.id: 'preview',
    media_asset_location.archive.id: 'archive_preview',
}


# ## FUNCTIONS

def check_context(func):
    def wrapper(*args):
        if not has_app_context():
            return None
        return func(*args)
    return wrapper


# ## CLASSES

class MediaAsset(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    md5 = DB.Column(BlobMD5(nullable=False), index=True, unique=True, nullable=False)
    width = DB.Column(DB.INTEGER, nullable=True)
    height = DB.Column(DB.INTEGER, nullable=True)
    size = DB.Column(DB.INTEGER, nullable=True)
    pixel_md5 = DB.Column(BlobMD5(nullable=True), nullable=True)
    duration = DB.Column(DB.REAL, nullable=True)
    audio = DB.Column(DB.BOOLEAN, nullable=True)
    file_ext = DB.Column(DB.TEXT, nullable=True)
    location, location_id, location_name, location_enum, location_filter, location_col =\
        get_relation_definitions(media_asset_location, relname='location', relcol='id', colname='location_id',
                                 tblname='media_asset', nullable=True)

    # ## Instance methods

    @property
    def is_video(self):
        return self.file_ext not in ['jpg', 'png', 'gif']

    @property
    def has_file_access(self):
        return self.location.name != 'alternate' or os.path.exists(ALTERNATE_MEDIA_DIRECTORY)

    # #### File system functions

    @property
    def original_file_path(self):
        path = ORIGINAL_FILE_PATHS.get(self.location_id)
        return self._full_path(path, self.file_ext)

    @property
    def image_sample_path(self):
        path = IMAGE_SAMPLE_FILE_PATHS.get(self.location_id)
        ext = IMAGE_SAMPLE_FILE_EXTS.get(self.location_id)
        if path and ext:
            return self._full_path(path, ext)

    @property
    def image_preview_path(self):
        path = IMAGE_PREVIEW_FILE_PATHS.get(self.location_id)
        ext = IMAGE_PREVIEW_FILE_EXTS.get(self.location_id)
        if path and ext:
            return self._full_path(path, ext)

    @property
    def video_sample_path(self):
        path = VIDEO_SAMPLE_FILE_PATHS.get(self.location_id)
        ext = VIDEO_SAMPLE_FILE_EXTS.get(self.location_id)
        if path and ext:
            return self._full_path(path, ext)

    @property
    def video_preview_path(self):
        path = VIDEO_SAMPLE_FILE_PATHS.get(self.location_id)
        ext = VIDEO_SAMPLE_FILE_EXTS.get(self.location_id)
        if self.is_video:
            return self._full_path(path, ext)

    # #### Network URL functions

    @classmethod
    def image_server_url(cls, urlpath, subtype):
        if HAS_EXTERNAL_IMAGE_SERVER:
            return cls._external_server_url(urlpath, subtype)
        return cls._internal_server_url(urlpath, subtype)

    @property
    @check_context
    def original_file_url(self):
        suburl_path = SUBURL_PATHS.get(self.location_id)
        subdir_path = ORIGINAL_SUBDIR_PATHS.get(self.location_id)
        if suburl_path and subdir_path:
            return self.image_server_url(subdir_path + self._partial_network_path + self.file_ext, suburl_path)

    @property
    @check_context
    def image_sample_url(self):
        suburl_path = SUBURL_PATHS.get(self.location_id)
        subdir_path = SAMPLE_SUBDIR_PATHS.get(self.location_id)
        if suburl_path:
            return self.image_server_url(subdir_path + self._partial_network_path + 'jpg', suburl_path)

    @property
    @check_context
    def image_preview_url(self):
        suburl_path = SUBURL_PATHS.get(self.location_id)
        subdir_path = PREVIEW_SUBDIR_PATHS.get(self.location_id)
        if suburl_path:
            return self.image_server_url(subdir_path + self._partial_network_path + 'jpg', suburl_path)

    @property
    @check_context
    def video_sample_url(self):
        suburl_path = SUBURL_PATHS.get(self.location_id)
        ext = VIDEO_SAMPLE_FILE_EXTS.get(self.location_id)
        if suburl_path:
            return self.image_server_url('video_sample' + self._partial_network_path + ext, suburl_path)

    @property
    @check_context
    def video_preview_url(self):
        suburl_path = SUBURL_PATHS.get(self.location_id)
        ext = VIDEO_SAMPLE_FILE_EXTS.get(self.location_id)
        if suburl_path:
            return self.image_server_url('video_preview' + self._partial_network_path + ext, suburl_path)

    # ## Private

    @staticmethod
    def _external_server_url(urlpath, subtype):
        return 'http://' + SERVER_INFO.addr + ':' + str(IMAGE_PORT) + f'/{subtype}/' + urlpath

    @staticmethod
    def _internal_server_url(urlpath, subtype):
        print('_internal_server_url', urlpath, subtype)
        return url_for('media.send_file', subtype=subtype, path=urlpath)

    def _full_path(self, path, ext):
        return path_join(path, self._partial_file_path + ext)

    @memoized_property
    def _partial_network_path(self):
        return '/%s/%s/%s.' % (self.md5[0:2], self.md5[2:4], self.md5)

    @memoized_property
    def _partial_file_path(self):
        return path_join(self.md5[0:2], self.md5[2:4], self._file_name)

    @memoized_property
    def _file_name(self):
        return '%s.' % (self.md5)
