# APP/SOURCES/BASE.PY

# ##PYTHON IMPORTS
import urllib

# ##LOCAL IMPORTS
from ..sites import GetSiteKey, GetSiteId, GetSiteDomain
from ..sources import SOURCES, SOURCEDICT
from ..logical.utility import GetHTTPFilename, GetFileExtension, SetError
from ..database.error_db import IsError


# ##GLOBAL VARIABLES

IMAGE_HEADERS = {}


# #### Classes

class NoSource():
    IMAGE_HEADERS = {}

    @staticmethod
    def SmallImageUrl(url):
        return url

    @staticmethod
    def NormalizedImageUrl(url):
        return url

    @staticmethod
    def GetMediaExtension(url):
        return GetFileExtension(GetHTTPFilename(url)).replace('jpeg', 'jpg')


# ##FUNCTIONS

# #### Utility functions

def GetImageSiteId(url):
    parse = urllib.parse.urlparse(url)
    return GetSiteId(parse.netloc)


# #### Source lookup functions

def GetPostSource(request_url):
    for source in SOURCES:
        if source.IsRequestUrl(request_url):
            return source


def GetArtistSource(artist_url):
    for source in SOURCES:
        if source.IsArtistUrl(artist_url):
            return source


def GetIllustSource(illust_url):
    for source in SOURCES:
        if source.IsPostUrl(illust_url):
            return source


def GetArtistIdSource(artist_url):
    for source in SOURCES:
        if source.IsArtistIdUrl(artist_url):
            return source


def GetImageSource(image_url):
    for source in SOURCES:
        if source.IsImageUrl(image_url):
            return source


# #### Param functions

def GetArtistRequiredParams(url):
    retdata = {'error': False}
    source = GetArtistSource(url)
    if source is None:
        return SetError(retdata, "Not a valid artist URL.")
    retdata['site_id'] = source.SITE_ID
    ret = source.GetArtistId(url)
    if ret is None:
        return SetError(retdata, "Unable to find site artist ID with URL.")
    if IsError(ret):
        return SetError(retdata, ret.message)
    retdata['site_artist_id'] = int(ret)
    return retdata


def GetIllustRequiredParams(url):
    retdata = {'error': False}
    source = GetIllustSource(url)
    if source is None:
        return SetError(retdata, "Not a valid illust URL.")
    retdata['site_id'] = source.SITE_ID
    ret = source.GetIllustId(url)
    if ret is None:
        return SetError(retdata, "Unable to find site illust ID with URL.")
    if IsError(ret):
        return SetError(retdata, ret.message)
    retdata['site_illust_id'] = int(ret)
    return retdata


# #### Other

def GetPreviewUrl(url, site_id):
    return url if site_id == 0 else 'https://' + GetSiteDomain(site_id) + url


# ##### Base source functions

"""These mirror the functions in the other source files, for when a source is not found"""


def GetSourceById(site_id):
    site_key = GetSiteKey(site_id)
    return SOURCEDICT[site_key]


def SmallImageUrl(image_url):
    return image_url


def NormalizedImageUrl(image_url):
    return image_url


def GetImageExtension(image_url):
    filename = GetHTTPFilename(image_url)
    return GetFileExtension(filename)


def GetMediaExtension(media_url):
    return GetImageExtension(media_url)
