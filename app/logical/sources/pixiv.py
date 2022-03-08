# APP/LOGICAL/SOURCES/PIXIV.PY

# ## PYTHON IMPORTS
import re
import time
import urllib
import datetime

# ## EXTERNAL IMPORTS
import requests

# ## PACKAGE IMPORTS
from config import PIXIV_PHPSESSID

# ## LOCAL IMPORTS
from ..utility import get_current_time, get_file_extension, get_http_filename, safe_get, fixup_crlf,\
    process_utc_timestring
from ..database.error_db import create_error, is_error
from ..database.api_data_db import get_api_artist, get_api_illust, get_api_data, save_api_data
from ..sites import Site, get_site_domain, get_site_id


# ### GLOBAL VARIABLES

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
^https?://[^.]+\.pximg\.net                 # Hostname
(?:/c/\w+)?                                 # Size 1
/(?:img-original|img-master|custom-thumb)   # Path
/img
/(\d{4}/\d{2}/\d{2}/\d{2}/\d{2}/\d{2})      # Date
/(\d+)_                                     # ID
p(\d+)                                      # Order
(?:_(?:master|square|custom)1200)?          # Size 2
\.(jpg|png|gif|mp4|zip)                     # Extension
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


# ## FUNCTIONS

# #### Auxiliary functions

def has_artist_urls(artist):
    return (artist.current_site_account is not None) or (len(artist.site_accounts) == 1)


def artist_main_url(artist):
    if not has_artist_urls(artist):
        return ""
    return ARTIST_HREFURL % artist.site_artist_id


def artist_artworks_url(artist):
    url = artist_main_url(artist)
    return url + '/artworks' if len(url) else ""


def artist_illustrations_url(artist):
    url = artist_main_url(artist)
    return url + '/illustrations' if len(url) else ""


def artist_manga_url(artist):
    url = artist_main_url(artist)
    return url + '/manga' if len(url) else ""


def artist_bookmarks_url(artist):
    url = artist_main_url(artist)
    return url + '/bookmarks/artworks' if len(url) else ""


def artist_booru_search_url(artist):
    return 'http://www.pixiv.net/member.php?id=%d/' % artist.site_artist_id


def get_data_illust_ids(pixiv_data, type):
    try:
        return list(map(int, pixiv_data[type].keys()))
    except Exception:
        return []


def is_post_url(url):
    return bool(ARTWORKS_RG.match(url))


def get_media_url(illust_url):
    if illust_url.site_id == 0:
        return illust_url.url
    return 'https://' + get_site_domain(illust_url.site_id) + illust_url.url


def get_post_url(illust):
    return ILLUST_HREFURL % illust.site_illust_id


def get_illust_url(site_illust_id):
    return ILLUST_HREFURL % site_illust_id


def illust_has_images(illust_url):
    return True


def illust_has_videos(illust_url):
    return False


def image_illust_download_urls(illust):
    return list(filter(lambda x: image_url_mapper, illust.urls))


def get_full_url(illust_url):
    return get_media_url(illust_url)


def image_url_mapper(x):
    return is_image_url(get_full_url(x))


def video_url_mapper(x):
    return is_video_url(get_full_url(x))


# Artist

def artist_links(artist):
    return {
        'main': artist_main_url(artist),
        'artworks': artist_artworks_url(artist),
        # 'illustrations': artist_illustrations_url(artist),
        # 'manga': artist_manga_url(artist),
        'bookmarks': artist_bookmarks_url(artist),
    }


# Tag

def tag_search_url(tag):
    return TAG_SEARCH_HREFURL % tag.name


#   URL

def get_image_extension(image_url):
    filename = get_http_filename(image_url)
    return get_file_extension(filename)


def get_media_extension(media_url):
    return get_image_extension(media_url)


def is_request_url(request_url):
    return ARTWORKS_RG.match(request_url) or IMAGE_RG.match(request_url)


def is_image_url(image_url):
    return bool(IMAGE_RG.match(image_url))


def is_video_url(video_url):
    return False


def is_artist_id_url(artist_url):
    return bool(USERS_RG.match(artist_url))


def get_artist_id(artist_url):
    match = USERS_RG.match(artist_url)
    if match:
        return match.group(1)


def is_artist_url(artist_url):
    return is_artist_id_url(artist_url)


def small_image_url(image_url):
    date, id, order, type = IMAGE_RG.match(image_url).groups()
    return IMAGE_SERVER + '/c/540x540_70/img-master/img/' + date + '/' + id + '_p' + order + '_master1200.jpg'


def normalized_image_url(image_url):
    return IMAGE_SERVER + normalize_image_url(image_url)


def get_illust_id(request_url):
    artwork_match = ARTWORKS_RG.match(request_url)
    if artwork_match:
        return int(artwork_match.group(1))
    image_match = IMAGE_RG.match(request_url)
    if image_match:
        return int(image_match.group(2))


def get_artist_id_url_id(artist_url):
    return get_artist_id(artist_url)


def normalize_image_url(image_url):
    image_url = urllib.parse.urlparse(image_url).path.replace('img-master', 'img-original')
    image_url = re.sub(r'_(?:master|square)1200', '', image_url)
    image_url = re.sub(r'(?:/c/\w+)', '', image_url)
    return image_url


#   Network

def pixiv_request(url):
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


def get_pixiv_illust(illust_id):
    print("Getting pixiv #%d" % illust_id)
    data = pixiv_request("https://www.pixiv.net/ajax/illust/%d" % illust_id)
    if data['error']:
        return create_error('logical.sources.pixiv.get_pixiv_illust', data['message'])
    return data['body']


def get_pixiv_artist(artist_id):
    print("Getting Pixiv user data...")
    data = pixiv_request("https://www.pixiv.net/ajax/user/%d?full=1" % artist_id)
    if data['error']:
        return create_error('logical.sources.pixiv.get_pixiv_artist', data['message'])
    return data['body']


def get_all_pixiv_artist_illusts(artist_id):
    data = pixiv_request('https://www.pixiv.net/ajax/user/%d/profile/all' % artist_id)
    if data['error']:
        return create_error('logical.sources.pixiv.get_all_pixiv_artist_illusts', data['message'])
    ids = get_data_illust_ids(data['body'], 'illusts')
    ids += get_data_illust_ids(data['body'], 'manga')
    return ids


def get_pixiv_page_data(site_illust_id):
    print("Downloading pages for pixiv #%d" % site_illust_id)
    data = pixiv_request("https://www.pixiv.net/ajax/illust/%s/pages" % site_illust_id)
    if data['error']:
        return create_error('logical.sources.pixiv.get_page_data', data['message'])
    return {'illustId': site_illust_id, 'pages': data['body']}


def get_pixiv_profile_data(site_artist_id):
    print("Downloading profile data for pxuser #%d" % site_artist_id)
    data = pixiv_request("https://www.pixiv.net/ajax/user/%d/profile/all" % site_artist_id)
    if data['error']:
        return create_error('logical.sources.pixiv.get_page_data', data['message'])
    return {'userId': site_artist_id, 'profile': data['body']}


# #### Param functions

def source_prework(site_illust_id):
    pass


# ###### ILLUST

def get_illust_tags(artwork):
    tags = set(tag_data['tag'] for tag_data in (safe_get(artwork, 'tags', 'tags') or []))
    if artwork['isOriginal']:
        tags.add('original')
    return list(tags)


def get_illust_urls_from_artwork(artwork):
    original_url = artwork['urls']['original']
    parse = urllib.parse.urlparse(original_url)
    site_id = get_site_id(parse.netloc)
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


def get_illust_urls_from_page(page_data):
    image_urls = []
    for i in range(len(page_data['pages'])):
        image = page_data['pages'][i]
        parse = urllib.parse.urlparse(image['urls']['original'])
        site_id = get_site_id(parse.netloc)
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


def get_illust_parameters_from_artwork(artwork, page_data):
    site_illust_id = int(artwork['illustId'])
    if page_data is None:
        illust_urls = get_illust_urls_from_artwork(artwork)
    else:
        illust_urls = get_illust_urls_from_page(page_data)
    sub_data = artwork['userIllusts'][str(site_illust_id)]
    return {
        'site_id': SITE_ID,
        'site_illust_id': site_illust_id,
        'site_created': process_utc_timestring(artwork['createDate']),
        'pages': artwork['pageCount'],
        'score': artwork['likeCount'],
        'site_uploaded': process_utc_timestring(artwork['uploadDate']),
        'site_updated': process_utc_timestring(sub_data['updateDate']),
        'title': artwork['title'],
        'bookmarks': artwork['bookmarkCount'],
        'replies': artwork['responseCount'],
        'views': artwork['viewCount'],
        'requery': get_current_time() + datetime.timedelta(days=1),
        'tags': get_illust_tags(artwork),
        'commentaries': safe_get(artwork, 'extraData', 'meta', 'twitter', 'description') or None,
        'illust_urls': illust_urls,
        'active': True,
        'site_artist_id': int(artwork['userId']),
    }


# ###### ARTIST

def get_pixiv_user_webpages(pxuser):
    webpages = set()
    if pxuser['webpage'] is not None:
        webpages.add(pxuser['webpage'])
    for site in pxuser['social']:
        webpages.add(pxuser['social'][site]['url'])
    return list(webpages)


def get_artist_parameters_from_pxuser(pxuser, artwork):
    return {
        'site_id': SITE_ID,
        'site_artist_id': int(pxuser['userId']),
        'site_created': None,
        'current_site_account': artwork['userAccount'] if artwork is not None else None,
        'requery': get_current_time() + datetime.timedelta(days=1),
        'active': True,
        'names': [pxuser['name']],
        'site_accounts': [artwork['userAccount']] if artwork is not None else [],
        'profiles': fixup_crlf(pxuser['comment']) or None,
        'webpages': get_pixiv_user_webpages(pxuser)
    }


# Data lookup functions

def get_page_data(site_illust_id):
    page_data = get_api_data([site_illust_id], SITE_ID, 'page')
    if len(page_data) == 0:
        page_data = get_pixiv_page_data(site_illust_id)
        if is_error(page_data):
            return
        save_api_data([page_data], 'illustId', SITE_ID, 'page')
    else:
        page_data = page_data[0].data
    return page_data


def get_profile_data(site_artist_id):
    profile_data = get_api_data([site_artist_id], SITE_ID, 'profile')
    if len(profile_data) == 0:
        profile_data = get_pixiv_profile_data(site_artist_id)
        if is_error(profile_data):
            return
        save_api_data([profile_data], 'userId', SITE_ID, 'profile')
    else:
        profile_data = profile_data[0].data
    return profile_data


def get_artist_api_data(site_artist_id):
    pxuser = get_api_artist(site_artist_id, SITE_ID)
    if pxuser is None:
        pxuser = get_pixiv_artist(site_artist_id)
        if is_error(pxuser):
            print("Error getting artist data!")
            return
        save_api_data([pxuser], 'userId', SITE_ID, 'artist')
    return pxuser


def get_artist_data(site_artist_id):
    pxuser = get_artist_api_data(site_artist_id)
    if pxuser is None:
        return {'active': False, 'requery': None}
    profile_data = get_profile_data(site_artist_id)
    artwork = None
    if not is_error(profile_data):
        artwork_ids = [int(artwork_id) for artwork_id in (safe_get(profile_data, 'profile', 'illusts') or {}).keys()]
        if len(artwork_ids):
            artworks = get_api_data(artwork_ids, SITE_ID, 'illust')
            if len(artworks):
                artwork = artworks[0].data
            else:
                artwork = get_illust_api_data(artwork_ids[0])
    return get_artist_parameters_from_pxuser(pxuser, artwork)


def get_illust_api_data(site_illust_id):
    artwork = get_api_illust(site_illust_id, SITE_ID)
    if artwork is None:
        artwork = get_pixiv_illust(site_illust_id)
        if is_error(artwork):
            print("Error getting illust data!")
            return
        save_api_data([artwork], 'illustId', SITE_ID, 'illust')
    return artwork


def get_illust_data(site_illust_id):
    artwork = get_illust_api_data(site_illust_id)
    if artwork is None:
        return {'active': False, 'requery': None}
    page_data = get_page_data(site_illust_id) if artwork['pageCount'] > 1 else None
    page_data = page_data if not is_error(page_data) else None
    return get_illust_parameters_from_artwork(artwork, page_data)


def get_artist_id_by_illust_id(site_illust_id):
    artwork = get_illust_api_data(site_illust_id)
    return safe_get(artwork, 'userId')
