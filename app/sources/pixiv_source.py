# APP/SOURCES/PIXIV.PY

# ##PYTHON IMPORTS
import re
import time
import urllib
import requests
import datetime

# ##LOCAL IMPORTS
from ..logical.utility import GetCurrentTime, GetFileExtension, GetHTTPFilename, SafeGet, FixupCRLF, ProcessUTCTimestring
from ..database.error_db import CreateError, IsError
from ..database.cache_db import GetApiArtist, GetApiIllust, GetApiData, SaveApiData
from ..config import PIXIV_PHPSESSID
from ..sites import Site, GetSiteDomain, GetSiteId


# ###GLOBAL VARIABLES

# #### Module variables

NAME = 'pixiv'

IMAGE_HEADERS = {
    'Referer': 'https://app-api.pixiv.net/'
}

BAD_ID_TAGS = ['bad_id', 'bad_pixiv_id']

ILLUST_SHORTLINK = 'pixiv #%d'
ARTIST_SHORTLINK = 'pxuser #%d'

ILLUST_HREFURL = 'https://www.pixiv.net/artworks/%d'
ARTIST_HREFURL = 'https://www.pixiv.net/users/%d'
TAG_SEARCH_HREFURL = 'https://www.pixiv.net/tags/%s/artworks'

SITE_ID = Site.PIXIV.value

HAS_TAG_SEARCH = True


# #### Regex variables

ARTWORKS_RG = re.compile(r"""
^https?://www\.pixiv\.net               # Hostname
/(?:en/)?artworks/                      # Path
(\d+)$                                  # ID
""", re.X | re.IGNORECASE)

USERS_RG = re.compile(r"""
^https?://www\.pixiv\.net               # Hostname
/(?:en/)?users/                         # Path
(\d+)$                                  # ID
""", re.X | re.IGNORECASE)

IMAGE_RG = re.compile(r"""
^https?://[^.]+\.pximg\.net             # Hostname
(?:/c/\w+)?                             # Size 1
/img-(?:original|master)/img            # Path
/(\d{4}/\d{2}/\d{2}/\d{2}/\d{2}/\d{2})  # Date
/(\d+)_                                 # ID
p(\d+)                                  # Order
(?:_(?:master|square)1200)?             # Size 2
\.(jpg|png|gif|mp4|zip)                 # Extension
""", re.X | re.IGNORECASE)


# #### Network variables

API_HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.9',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) Waterfox/56.2'
}

API_JAR = requests.cookies.RequestsCookieJar()
API_JAR.set('PHPSESSID', PIXIV_PHPSESSID, domain='.pixiv.net', path='/', expires=None)


# #### Other variables

IMAGE_SERVER = 'https://i.pximg.net'


# ##FUNCTIONS

#   AUXILIARY

def HasArtistUrls(artist):
    return (artist.current_site_account is not None) or (len(artist.site_accounts) == 1)


def ArtistMainUrl(artist):
    if not HasArtistUrls(artist):
        return ""
    return ARTIST_HREFURL % artist.site_artist_id


def ArtistArtworksUrl(artist):
    url = ArtistMainUrl(artist)
    return url + '/artworks' if len(url) else ""


def ArtistIllustrationsUrl(artist):
    url = ArtistMainUrl(artist)
    return url + '/illustrations' if len(url) else ""


def ArtistMangaUrl(artist):
    url = ArtistMainUrl(artist)
    return url + '/manga' if len(url) else ""


def ArtistBookmarksUrl(artist):
    url = ArtistMainUrl(artist)
    return url + '/bookmarks/artworks' if len(url) else ""


def ArtistBooruSearchUrl(artist):
    return 'http://www.pixiv.net/member.php?id=%d/' % artist.site_artist_id


def GetDataIllustIDs(pixiv_data, type):
    try:
        return list(map(int, pixiv_data[type].keys()))
    except Exception:
        return []


def IsPostUrl(url):
    return bool(ARTWORKS_RG.match(url))


def GetMediaUrl(illust_url):
    return illust_url.url if illust_url.site_id == 0 else 'https://' + GetSiteDomain(illust_url.site_id) + illust_url.url


def GetPostUrl(illust):
    return ILLUST_HREFURL % illust.site_illust_id


def GetIllustUrl(site_illust_id):
    return ILLUST_HREFURL % site_illust_id


def IllustHasImages(illust_url):
    return True


def IllustHasVideos(illust_url):
    return False


def ImageIllustDownloadUrls(illust):
    return list(filter(lambda x: ImageUrlMapper, illust.urls))


def GetFullUrl(illust_url):
    return GetMediaUrl(illust_url)


def ImageUrlMapper(x):
    return IsImageUrl(GetFullUrl(x))


def VideoUrlMapper(x):
    return IsVideoUrl(GetFullUrl(x))


# Artist

def ArtistLinks(artist):
    return {
        'main': ArtistMainUrl(artist),
        'artworks': ArtistArtworksUrl(artist),
        # 'illustrations': ArtistIllustrationsUrl(artist),
        # 'manga': ArtistMangaUrl(artist),
        'bookmarks': ArtistBookmarksUrl(artist),
    }


# Tag

def TagSearchUrl(tag):
    return TAG_SEARCH_HREFURL % tag.name


#   URL

def GetImageExtension(image_url):
    filename = GetHTTPFilename(image_url)
    return GetFileExtension(filename)


def GetMediaExtension(media_url):
    return GetImageExtension(media_url)


def IsRequestUrl(request_url):
    return ARTWORKS_RG.match(request_url) or IMAGE_RG.match(request_url)


def IsImageUrl(image_url):
    return bool(IMAGE_RG.match(image_url))


def IsVideoUrl(video_url):
    return False


def IsArtistIdUrl(artist_url):
    return bool(USERS_RG.match(artist_url))


def GetArtistId(artist_url):
    match = USERS_RG.match(artist_url)
    if match:
        return match.group(1)


def IsArtistUrl(artist_url):
    return IsArtistIdUrl(artist_url)


def SmallImageUrl(image_url):
    date, id, order, type = IMAGE_RG.match(image_url).groups()
    return IMAGE_SERVER + '/c/540x540_70/img-master/img/' + date + '/' + id + '_p' + order + '_master1200.jpg'


def NormalizedImageUrl(image_url):
    return IMAGE_SERVER + NormalizeImageURL(image_url)


def GetUploadType(request_url):
    artwork_match = ARTWORKS_RG.match(request_url)
    if artwork_match:
        return 'post'
    image_match = IMAGE_RG.match(request_url)
    if image_match:
        return 'image'


def GetIllustId(request_url):
    artwork_match = ARTWORKS_RG.match(request_url)
    if artwork_match:
        return int(artwork_match.group(1))
    image_match = IMAGE_RG.match(request_url)
    if image_match:
        return int(image_match.group(2))


def GetUploadInfo(request_url):
    artwork_match = ARTWORKS_RG.match(request_url)
    if artwork_match:
        illust_id = int(artwork_match.group(1))
        type = 'post'
    image_match = IMAGE_RG.match(request_url) if artwork_match is None else None
    if image_match:
        illust_id = int(image_match.group(2))
        type = 'image'
    return type, illust_id


def SubscriptionCheck(request_url):
    artist_id = None
    artwork_match = USERS_RG.match(request_url)
    if artwork_match:
        artist_id = int(artwork_match.group(1))
    return artist_id


def NormalizeImageURL(image_url):
    image_url = urllib.parse.urlparse(image_url).path.replace('img-master', 'img-original')
    image_url = re.sub(r'_(?:master|square)1200', '', image_url)
    image_url = re.sub(r'(?:/c/\w+)', '', image_url)
    return image_url


#   Network

def PixivRequest(url):
    for i in range(3):
        try:
            response = requests.get(url, headers=API_HEADERS, cookies=API_JAR, timeout=10)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            if i == 2:
                print("Connection errors exceeded!")
                return {'error': True, 'message': repr(e)}
            print("Pausing for network timeout...")
            time.sleep(5)
            continue
        if response.status_code == 200:
            break
        print("\n%s\nHTTP %d: %s (%s)" % (url, response.status_code, response.reason, response.text))
        return {'error': True, 'message': "HTTP %d - %s" % (response.status_code, response.reason)}
    try:
        return response.json()
    except Exception:
        return {'error': True, 'message': "Error decoding response into JSON."}


def GetPixivIllust(illust_id):
    print("Getting pixiv #%d" % illust_id)
    data = PixivRequest("https://www.pixiv.net/ajax/illust/%d" % illust_id)
    if data['error']:
        return CreateError('sources.pixiv.GetPixivIllust', data['message'])
    return data['body']


def GetPixivArtist(artist_id):
    print("Getting Pixiv user data...")
    data = PixivRequest("https://www.pixiv.net/ajax/user/%d?full=1" % artist_id)
    if data['error']:
        return CreateError('sources.pixiv.GetPixivArtist', data['message'])
    return data['body']


def GetAllPixivArtistIllusts(artist_id):
    data = PixivRequest('https://www.pixiv.net/ajax/user/%d/profile/all' % artist_id)
    if data['error']:
        return CreateError('sources.pixiv.GetAllPixivArtistIllusts', data['message'])
    ids = GetDataIllustIDs(data['body'], 'illusts')
    ids += GetDataIllustIDs(data['body'], 'manga')
    return ids


def GetPixivPageData(site_illust_id):
    print("Downloading pages for pixiv #%d" % site_illust_id)
    data = PixivRequest("https://www.pixiv.net/ajax/illust/%s/pages" % site_illust_id)
    if data['error']:
        return CreateError('sources.pixiv.GetPageData', data['message'])
    return {'illustId': site_illust_id, 'pages': data['body']}


def GetPixivProfileData(site_artist_id):
    print("Downloading profile data for pxuser #%d" % site_artist_id)
    data = PixivRequest("https://www.pixiv.net/ajax/user/%d/profile/all" % site_artist_id)
    if data['error']:
        return CreateError('sources.pixiv.GetPageData', data['message'])
    return {'userId': site_artist_id, 'profile': data['body']}


# #### Param functions

def Prework(site_illust_id):
    pass


# ###### ILLUST

def GetIllustTags(artwork):
    tags = set(tag_data['tag'] for tag_data in (SafeGet(artwork, 'tags', 'tags') or []))
    if artwork['isOriginal']:
        tags.add('original')
    return list(tags)


def GetIllustUrlsFromArtwork(artwork):
    original_url = artwork['urls']['original']
    parse = urllib.parse.urlparse(original_url)
    site_id = GetSiteId(parse.netloc)
    url = parse.path if site_id != 0 else original_url
    return [
        {
            'site_id': site_id,
            'url': url,
            'width': artwork['width'],
            'height': artwork['height'],
            'order': 1,
            'active': True,
        }
    ]


def GetIllustUrlsFromPage(page_data):
    image_urls = []
    for i in range(len(page_data['pages'])):
        image = page_data['pages'][i]
        parse = urllib.parse.urlparse(image['urls']['original'])
        site_id = GetSiteId(parse.netloc)
        url = parse.path if site_id != 0 else image['urls']['original']
        image_urls.append(
            {
                'site_id': site_id,
                'url': url,
                'width': image['width'],
                'height': image['height'],
                'order': i + 1,
                'active': True,
            }
        )
    return image_urls


def GetIllustParametersFromArtwork(artwork, page_data):
    site_illust_id = int(artwork['illustId'])
    illust_urls = GetIllustUrlsFromPage(page_data) if page_data is not None else GetIllustUrlsFromArtwork(artwork)
    sub_data = artwork['userIllusts'][str(site_illust_id)]
    return {
        'site_id': SITE_ID,
        'site_illust_id': site_illust_id,
        'site_created': ProcessUTCTimestring(artwork['createDate']),
        'pages': artwork['pageCount'],
        'score': artwork['likeCount'],
        'site_uploaded': ProcessUTCTimestring(artwork['uploadDate']),
        'site_updated': ProcessUTCTimestring(sub_data['updateDate']),
        'title': artwork['title'],
        'bookmarks': artwork['bookmarkCount'],
        'replies': artwork['responseCount'],
        'views': artwork['viewCount'],
        'requery': GetCurrentTime() + datetime.timedelta(days=1),
        'tags': GetIllustTags(artwork),
        'commentaries': SafeGet(artwork, 'extraData', 'meta', 'twitter', 'description') or None,
        'illust_urls': illust_urls,
        'active': True,
        'site_artist_id': int(artwork['userId']),
    }


# ###### ARTIST

def GetPixivUserWebpages(pxuser):
    webpages = set()
    if pxuser['webpage'] is not None:
        webpages.add(pxuser['webpage'])
    for site in pxuser['social']:
        webpages.add(pxuser['social'][site]['url'])
    return list(webpages)


def GetArtistParametersFromPxuser(pxuser, artwork):
    return {
        'site_id': SITE_ID,
        'site_artist_id': int(pxuser['userId']),
        'site_created': None,
        'current_site_account': artwork['userAccount'] if artwork is not None else None,
        'requery': GetCurrentTime() + datetime.timedelta(days=1),
        'active': True,
        'names': [pxuser['name']],
        'site_accounts': [artwork['userAccount']] if artwork is not None else [],
        'profiles': FixupCRLF(pxuser['comment']) or None,
        'webpages': GetPixivUserWebpages(pxuser)
    }


# Data lookup functions

def GetPageData(site_illust_id):
    page_data = GetApiData([site_illust_id], SITE_ID, 'page')
    if len(page_data) == 0:
        page_data = GetPixivPageData(site_illust_id)
        if IsError(page_data):
            return
        SaveApiData([page_data], 'illustId', SITE_ID, 'page')
    else:
        page_data = page_data[0].data
    return page_data


def GetProfileData(site_artist_id):
    profile_data = GetApiData([site_artist_id], SITE_ID, 'profile')
    if len(profile_data) == 0:
        profile_data = GetPixivProfileData(site_artist_id)
        if IsError(profile_data):
            return
        SaveApiData([profile_data], 'userId', SITE_ID, 'profile')
    else:
        profile_data = profile_data[0].data
    return profile_data


def GetArtistApiData(site_artist_id):
    pxuser = GetApiArtist(site_artist_id, SITE_ID)
    if pxuser is None:
        pxuser = GetPixivArtist(site_artist_id)
        if IsError(pxuser):
            print("Error getting artist data!")
            return
        SaveApiData([pxuser], 'userId', SITE_ID, 'artist')
    return pxuser


def GetArtistData(site_artist_id):
    pxuser = GetArtistApiData(site_artist_id)
    if pxuser is None:
        return {'active': False, 'requery': None}
    profile_data = GetProfileData(site_artist_id)
    artwork = None
    if not IsError(profile_data):
        artwork_ids = [int(artwork_id) for artwork_id in (SafeGet(profile_data, 'profile', 'illusts') or {}).keys()]
        if len(artwork_ids):
            artworks = GetApiData(artwork_ids, SITE_ID, 'illust')
            if len(artworks):
                artwork = artworks[0].data
            else:
                artwork = GetIllustApiData(artwork_ids[0])
    return GetArtistParametersFromPxuser(pxuser, artwork)


def GetIllustApiData(site_illust_id):
    artwork = GetApiIllust(site_illust_id, SITE_ID)
    if artwork is None:
        artwork = GetPixivIllust(site_illust_id)
        if IsError(artwork):
            print("Error getting illust data!")
            return
        SaveApiData([artwork], 'illustId', SITE_ID, 'illust')
    return artwork


def GetIllustData(site_illust_id):
    artwork = GetIllustApiData(site_illust_id)
    if artwork is None:
        return {'active': False, 'requery': None}
    page_data = GetPageData(site_illust_id) if artwork['pageCount'] > 1 else None
    page_data = page_data if not IsError(page_data) else None
    return GetIllustParametersFromArtwork(artwork, page_data)


def GetArtistIdByIllustId(site_illust_id):
    artwork = GetIllustApiData(site_illust_id)
    return SafeGet(artwork, 'userId')
