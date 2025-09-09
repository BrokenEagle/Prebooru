# APP/LOGICAL/SOURCES/BASE_SRC.PY

# ## PACKAGE IMPORTS
from utility.file import get_http_filename, get_file_extension

# ## LOCAL IMPORTS
from ...models.model_enums import SiteDescriptor
from ..utility import set_error
from ..database.error_db import is_error


# ## CLASSES

class NoSource():
    """These mirror the functions in the other source files, for when a source is not found"""

    SITE = SiteDescriptor.custom

    IMAGE_HEADERS = {}

    @staticmethod
    def get_full_url(illust_url):
        return illust_url.url

    @staticmethod
    def get_primary_url(illust):
        return illust.site_url

    @staticmethod
    def is_video_url(url):
        return get_file_extension(get_http_filename(url)) in ['mp4']

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
    def get_media_url(illust_url):
        return illust_url.url

    @staticmethod
    def get_preview_url(illust_url):
        return illust_url.url

    @staticmethod
    def video_url_mapper(illust_url):
        return illust_url.sample_site_id is not None and illust_url.sample_url is not None

    @staticmethod
    def image_url_mapper(illust_url):
        return illust_url.sample_site_id is None and illust_url.sample_url is None

    @staticmethod
    def get_media_extension(url):
        return get_file_extension(get_http_filename(url)).replace('jpeg', 'jpg')

    @staticmethod
    def artist_booru_search_url(url):
        return None


# ## FUNCTIONS

# #### Source lookup functions

def get_post_source(request_url):
    for source in _source_iterator():
        if source.is_request_url(request_url):
            return source


def get_artist_source(artist_url):
    for source in _source_iterator():
        if source.is_artist_url(artist_url):
            return source


def get_artist_id_source(artist_url):
    for source in _source_iterator():
        if source.is_artist_id_url(artist_url):
            return source


def get_media_source(image_url):
    for source in _source_iterator():
        if source.is_image_url(image_url) or source.is_video_url(image_url):
            return source
    return NoSource


# #### Param functions

def get_artist_required_params(url):
    retdata = {'error': False}
    source = get_artist_source(url)
    if source is None:
        return set_error(retdata, "Not a valid artist URL.")
    retdata['site_name'] = source.SITE.name
    ret = source.get_artist_id(url)
    if ret is None:
        return set_error(retdata, "Unable to find site artist ID with URL.")
    if is_error(ret):
        return set_error(retdata, ret.message)
    retdata['site_artist_id'] = int(ret)
    return retdata


# #### Private

def _source_iterator():
    from ..sources import SOURCES
    for source in SOURCES:
        yield source
