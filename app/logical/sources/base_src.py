# APP/LOGICAL/SOURCES/BASE_SRC.PY

# ## PACKAGE IMPORTS
from utility.file import get_http_filename, get_file_extension

# ## LOCAL IMPORTS
from ...enum_imports import site_descriptor
from ..utility import set_error
from ..database.error_db import is_error


# ## CLASSES

class NoSource():
    """These mirror the functions in the other source files, for when a source is not found"""

    SITE = site_descriptor.custom

    IMAGE_HEADERS = {}

    @staticmethod
    def original_image_url(url):
        return url

    @staticmethod
    def small_image_url(url):
        return url

    @staticmethod
    def normalized_image_url(url):
        return url

    @staticmethod
    def partial_media_url(url):
        return url

    @staticmethod
    def get_illust_id(url):
        return None

    @staticmethod
    def get_media_extension(url):
        return get_file_extension(get_http_filename(url)).replace('jpeg', 'jpg')

    @staticmethod
    def artist_booru_search_url(url):
        return None


# ## FUNCTIONS

# #### Source lookup functions

def get_post_source(request_url):
    _import_package()
    for source in SOURCES:
        if source.is_request_url(request_url):
            return source


def get_artist_source(artist_url):
    _import_package()
    for source in SOURCES:
        if source.is_artist_url(artist_url):
            return source


def get_illust_source(illust_url):
    _import_package()
    for source in SOURCES:
        if source.is_post_url(illust_url):
            return source


def get_artist_id_source(artist_url):
    _import_package()
    for source in SOURCES:
        if source.is_artist_id_url(artist_url):
            return source


def get_media_source(image_url):
    _import_package()
    for source in SOURCES:
        if source.is_image_url(image_url) or source.is_video_url(image_url):
            return source
    return NoSource


# #### Param functions

def get_artist_required_params(url):
    retdata = {'error': False}
    source = get_artist_source(url)
    if source is None:
        return set_error(retdata, "Not a valid artist URL.")
    retdata['site'] = source.SITE
    ret = source.get_artist_id(url)
    if ret is None:
        return set_error(retdata, "Unable to find site artist ID with URL.")
    if is_error(ret):
        return set_error(retdata, ret.message)
    retdata['site_artist_id'] = int(ret)
    return retdata


# #### Private

def _import_package():
    global SOURCES, SOURCEDICT
    from ..sources import SOURCES, SOURCEDICT
