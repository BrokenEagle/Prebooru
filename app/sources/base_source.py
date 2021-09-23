# APP/SOURCES/BASE.PY

# ##PYTHON IMPORTS
import urllib

# ##LOCAL IMPORTS
from ..logical.sites import get_site_key, get_site_id, get_site_domain
from ..sources import SOURCES, SOURCEDICT
from ..logical.utility import get_http_filename, get_file_extension, set_error
from ..database.error_db import is_error


# #### Classes

class NoSource():
    """These mirror the functions in the other source files, for when a source is not found"""

    IMAGE_HEADERS = {}

    @staticmethod
    def small_image_url(url):
        return url

    @staticmethod
    def normalized_image_url(url):
        return url

    @staticmethod
    def get_media_extension(url):
        return get_file_extension(get_http_filename(url)).replace('jpeg', 'jpg')


# ##FUNCTIONS

# #### Utility functions

def get_image_site_id(url):
    parse = urllib.parse.urlparse(url)
    return get_site_id(parse.netloc)


# #### Source lookup functions

def get_post_source(request_url):
    for source in SOURCES:
        if source.is_request_url(request_url):
            return source


def get_artist_source(artist_url):
    for source in SOURCES:
        if source.is_artist_url(artist_url):
            return source


def get_illust_source(illust_url):
    for source in SOURCES:
        if source.is_post_url(illust_url):
            return source


def get_artist_id_source(artist_url):
    for source in SOURCES:
        if source.is_artist_id_url(artist_url):
            return source


def get_image_source(image_url):
    for source in SOURCES:
        if source.is_image_url(image_url):
            return source


# #### Param functions

def get_artist_required_params(url):
    retdata = {'error': False}
    source = get_artist_source(url)
    if source is None:
        return set_error(retdata, "Not a valid artist URL.")
    retdata['site_id'] = source.SITE_ID
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
    retdata['site_id'] = source.SITE_ID
    ret = source.get_illust_id(url)
    if ret is None:
        return set_error(retdata, "Unable to find site illust ID with URL.")
    if is_error(ret):
        return set_error(retdata, ret.message)
    retdata['site_illust_id'] = int(ret)
    return retdata


# #### Other

def get_preview_url(url, site_id):
    return url if site_id == 0 else 'https://' + get_site_domain(site_id) + url


def get_source_by_id(site_id):
    site_key = get_site_key(site_id)
    return SOURCEDICT[site_key]
