# APP/LOGICAL/SOURCES/BASE.PY

# ## PYTHON IMPORTS
import urllib

# ## PACKAGE IMPORTS
from utility.file import get_http_filename, get_file_extension

# ## LOCAL IMPORTS
from ..sites import get_site_key, get_site_from_domain, get_site_domain
from ..utility import set_error
from ..database.error_db import is_error


# ## CLASSES

class NoSource():
    """These mirror the functions in the other source files, for when a source is not found"""

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
    def get_media_extension(url):
        return get_file_extension(get_http_filename(url)).replace('jpeg', 'jpg')

    @staticmethod
    def artist_booru_search_url(url):
        return None


# ## FUNCTIONS

# #### Utility functions

def get_image_site(url):
    parse = urllib.parse.urlparse(url)
    return get_site_from_domain(parse.netloc)


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


def get_illust_required_params(url):
    retdata = {'error': False}
    source = get_illust_source(url)
    if source is None:
        return set_error(retdata, "Not a valid illust URL.")
    retdata['site'] = source.SITE
    ret = source.get_illust_id(url)
    if ret is None:
        return set_error(retdata, "Unable to find site illust ID with URL.")
    if is_error(ret):
        return set_error(retdata, ret.message)
    retdata['site_illust_id'] = int(ret)
    return retdata


def get_illust_url_params(media_url):
    source = get_media_source(media_url)
    site = get_image_site(media_url)
    partial_url = source.partial_media_url(media_url)
    return site, partial_url


# #### Other

def get_preview_url(url, site):
    return url if site == 0 else 'https://' + get_site_domain(site) + url


def get_source_by_id(site):
    _import_package()
    site_key = get_site_key(site)
    return SOURCEDICT[site_key]


# #### Private

def _import_package():
    global SOURCES, SOURCEDICT
    from ..sources import SOURCES, SOURCEDICT
