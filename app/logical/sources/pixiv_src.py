# APP/LOGICAL/SOURCES/PIXIV_SRC.PY

# ## PYTHON IMPORTS
import re
import time
import urllib

# ## EXTERNAL IMPORTS
import requests

# ## PACKAGE IMPORTS
from config import PIXIV_PHPSESSID
from utility.data import safe_get, fixup_crlf
from utility.time import get_current_time, process_utc_timestring
from utility.file import get_file_extension, get_http_filename
from utility.uprint import print_info

# ## LOCAL IMPORTS
from ...enum_imports import site_descriptor, api_data_type
from ..database.error_db import create_error, is_error
from ..database.api_data_db import get_api_artist, get_api_illust, get_api_data, save_api_data
from ..database.server_info_db import get_next_wait, update_next_wait


# ### GLOBAL VARIABLES

# #### Module variables

IMAGE_HEADERS = {
    'Referer': 'https://www.pixiv.net/'
}

BAD_ID_TAGS = ['bad_id', 'bad_pixiv_id']

ILLUST_SHORTLINK = 'pixiv #%d'
ARTIST_SHORTLINK = 'pxuser #%d'

ILLUST_HREFURL = 'https://www.pixiv.net/artworks/%d'
ARTIST_HREFURL = 'https://www.pixiv.net/users/%d'
TAG_SEARCH_HREFURL = 'https://www.pixiv.net/tags/%s/artworks'

SITE = site_descriptor.pixiv

HAS_TAG_SEARCH = True

# #### Regex variables

# ###### Hostname regexes

PIXIV_HOST_RG = re.compile(r'^^https?://www\.pixiv\.net', re.IGNORECASE)
PXIMG_HOST_RG = re.compile(r'https?://[^.]+\.pximg\.net', re.IGNORECASE)

# ###### Partial URL regexes

ARTWORKS_PARTIAL_RG = re.compile(r"""
/(?:en/)?artworks/                      # Path
(\d+)$                                  # ID
""", re.X | re.IGNORECASE)

USERS_PARTIAL_RG = re.compile(r"""
/(?:en/)?users/                         # Path
(\d+)$                                  # ID
""", re.X | re.IGNORECASE)

IMAGE_PARTIAL_RG = re.compile(r"""
(?:/c/\w+)?                                 # Size 1
/(?:img-original|img-master|custom-thumb)   # Path
/img
/(\d{4}/\d{2}/\d{2}/\d{2}/\d{2}/\d{2})      # Date
/(\d+)_                                     # ID
p(\d+)                                      # Order
(?:_(?:master|square|custom)1200)?          # Size 2
\.(jpg|png|gif|mp4|zip)                     # Extension
""", re.X | re.IGNORECASE)

# ###### Full URL Regexes

ARTWORKS_RG = re.compile(f'{PIXIV_HOST_RG.pattern}{ARTWORKS_PARTIAL_RG.pattern}', re.X | re.IGNORECASE)

USERS_RG = re.compile(f'{PIXIV_HOST_RG.pattern}{USERS_PARTIAL_RG.pattern}', re.X | re.IGNORECASE)

IMAGE_RG = re.compile(f'{PXIMG_HOST_RG.pattern}{IMAGE_PARTIAL_RG.pattern}', re.X | re.IGNORECASE)

# #### Network variables

API_HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',  # noqa: E501
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'en-US,en;q=0.9',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'  # noqa: E501
}

API_JAR = requests.cookies.RequestsCookieJar()
API_JAR.set('PHPSESSID', PIXIV_PHPSESSID, domain='.pixiv.net', path='/', expires=None)

# #### Other variables

IMAGE_SERVER = 'https://i.pximg.net'

MINIMUM_QUERY_INTERVAL = 2


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
    return 'https://www.pixiv.net/users/%d' % artist.site_artist_id


def get_data_illust_ids(pixiv_data, type):
    try:
        return list(map(int, pixiv_data[type].keys()))
    except Exception:
        return []


def is_post_url(url):
    return bool(ARTWORKS_RG.match(url))


def get_media_url(illust_url):
    return 'https://' + illust_url.site.domain + illust_url.url


def get_post_url(illust):
    return ILLUST_HREFURL % illust.site_illust_id


def get_illust_url(site_illust_id):
    return ILLUST_HREFURL % site_illust_id


def image_illust_download_urls(illust):
    return list(filter(lambda x: image_url_mapper, illust.urls))


def get_full_url(illust_url):
    return get_media_url(illust_url)


def get_alternate_url(illust_url):
    pass


def get_preview_url(illust_url):
    return small_image_url(get_full_url(illust_url))


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


def is_media_url(url):
    return is_image_url(url) or is_video_url(url)


def is_partial_media_url(url):
    return is_partial_image_url(url) or is_partial_video_url(url)


def is_image_url(image_url):
    return bool(IMAGE_RG.match(image_url))


def is_partial_image_url(image_url):
    return bool(IMAGE_PARTIAL_RG.match(image_url))


def is_video_url(video_url):
    return False


def is_partial_video_url(video_url):
    return False


def get_domain_from_partial_url(url):
    if is_partial_image_url(url):
        return 'i.pximg.net'


def is_artist_id_url(artist_url):
    return bool(USERS_RG.match(artist_url))


def get_artist_id(artist_url):
    match = USERS_RG.match(artist_url)
    if match:
        return match.group(1)


def is_artist_url(artist_url):
    return is_artist_id_url(artist_url)


def original_image_url(image_url):
    return normalized_image_url(image_url)


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

def check_request_wait(wait):
    if not wait:
        return
    next_wait = get_next_wait('pixiv')
    if next_wait is not None:
        sleep_time = next_wait - get_current_time().timestamp()
        if sleep_time > 0.0:
            update_next_wait('pixiv', MINIMUM_QUERY_INTERVAL + sleep_time)
            print_info("Pixiv request: sleeping -", sleep_time)
            time.sleep(sleep_time)
            return
    update_next_wait('pixiv', MINIMUM_QUERY_INTERVAL)


def pixiv_request(url, wait=True):
    check_request_wait(wait)
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
        return create_error('sources.pixiv.get_pixiv_illust', data['message'])
    return data['body']


def get_pixiv_artist(artist_id):
    print("Getting Pixiv user data...")
    data = pixiv_request("https://www.pixiv.net/ajax/user/%d?full=1" % artist_id)
    if data['error']:
        return create_error('sources.pixiv.get_pixiv_artist', data['message'])
    return data['body']


def get_all_pixiv_artist_illusts(artist_id):
    data = pixiv_request('https://www.pixiv.net/ajax/user/%d/profile/all' % artist_id)
    if data['error']:
        return create_error('sources.pixiv.get_all_pixiv_artist_illusts', data['message'])
    ids = get_data_illust_ids(data['body'], 'illusts')
    ids += get_data_illust_ids(data['body'], 'manga')
    return ids


def get_pixiv_page_data(site_illust_id):
    print("Downloading pages for pixiv #%d" % site_illust_id)
    data = pixiv_request("https://www.pixiv.net/ajax/illust/%s/pages" % site_illust_id)
    if data['error']:
        return create_error('sources.pixiv.get_page_data', data['message'])
    return {'illustId': site_illust_id, 'pages': data['body']}


def get_pixiv_profile_data(site_artist_id):
    print("Downloading profile data for pxuser #%d" % site_artist_id)
    data = pixiv_request("https://www.pixiv.net/ajax/user/%d/profile/all" % site_artist_id)
    if data['error']:
        return create_error('sources.pixiv.get_page_data', data['message'])
    return {'userId': site_artist_id, 'profile': data['body']}


# #### Param functions

def source_prework(site_illust_id):
    pass


# ###### ILLUST

def get_artwork_commentary(artwork):
    description = artwork['description']
    if len(description) > 0:
        description = safe_get(artwork, 'extraData', 'meta', 'twitter', 'description')
    return description if len(description) else None


def get_illust_tags(artwork):
    tags = set(tag_data['tag'] for tag_data in (safe_get(artwork, 'tags', 'tags') or []))
    if artwork['isOriginal']:
        tags.add('original')
    return list(tags)


def get_illust_urls_from_artwork(artwork):
    original_url = artwork['urls']['original']
    parse = urllib.parse.urlparse(original_url)
    site = site_descriptor.get_site_from_domain(parse.netloc)
    return [
        {
            'site_id': site.id,
            'url': parse.path,
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
        site = site_descriptor.get_site_from_domain(parse.netloc)
        image_urls.append(
            {
                'site_id': site.id,
                'url': parse.path,
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
        'site_id': SITE.id,
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
        'tags': get_illust_tags(artwork),
        'commentaries': get_artwork_commentary(artwork),
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
        'site_id': SITE.id,
        'site_artist_id': int(pxuser['userId']),
        'site_created': None,
        'current_site_account': artwork['userAccount'] if artwork is not None else None,
        'active': True,
        'names': [pxuser['name']],
        'site_accounts': [artwork['userAccount']] if artwork is not None else [],
        'profiles': fixup_crlf(pxuser['comment']) or None,
        'webpages': get_pixiv_user_webpages(pxuser)
    }


# Data lookup functions

def get_page_data(site_illust_id):
    page_data = get_api_data([site_illust_id], SITE.id, api_data_type.page.id)
    if len(page_data) == 0:
        page_data = get_pixiv_page_data(site_illust_id)
        if is_error(page_data):
            return
        save_api_data([page_data], 'illustId', SITE.id, api_data_type.page.id)
    else:
        page_data = page_data[0].data
    return page_data


def get_profile_data(site_artist_id):
    profile_data = get_api_data([site_artist_id], SITE.id, api_data_type.profile.id)
    if len(profile_data) == 0:
        profile_data = get_pixiv_profile_data(site_artist_id)
        if is_error(profile_data):
            return
        save_api_data([profile_data], 'userId', SITE.id, api_data_type.profile.id)
    else:
        profile_data = profile_data[0].data
    return profile_data


def get_artist_api_data(site_artist_id):
    pxuser = get_api_artist(site_artist_id, SITE.id)
    if pxuser is None:
        pxuser = get_pixiv_artist(site_artist_id)
        if is_error(pxuser):
            print("Error getting artist data!")
            return
        save_api_data([pxuser], 'userId', SITE.id, api_data_type.artist.id)
    return pxuser


def get_artist_data(site_artist_id):
    pxuser = get_artist_api_data(site_artist_id)
    if pxuser is None:
        return {'active': False}
    profile_data = get_profile_data(site_artist_id)
    artwork = None
    if not is_error(profile_data):
        artwork_ids = [int(artwork_id) for artwork_id in (safe_get(profile_data, 'profile', 'illusts') or {}).keys()]
        artwork_ids += [int(artwork_id) for artwork_id in (safe_get(profile_data, 'profile', 'manga') or {}).keys()]
        if len(artwork_ids):
            artworks = get_api_data(artwork_ids, SITE.id, api_data_type.illust.id)
            if len(artworks):
                artwork = artworks[0].data
            else:
                artwork = get_illust_api_data(artwork_ids[0])
    if artwork is None:
        raise Exception(f"Unable to find artwork for pxuser #{site_artist_id}")
    return get_artist_parameters_from_pxuser(pxuser, artwork)


def get_illust_api_data(site_illust_id):
    artwork = get_api_illust(site_illust_id, SITE.id)
    if artwork is None:
        artwork = get_pixiv_illust(site_illust_id)
        if is_error(artwork):
            print("Error getting illust data!")
            return
        save_api_data([artwork], 'illustId', SITE.id, api_data_type.illust.id)
    return artwork


def get_illust_data(site_illust_id):
    artwork = get_illust_api_data(site_illust_id)
    if artwork is None:
        return {'active': False}
    page_data = get_page_data(site_illust_id) if artwork['pageCount'] > 1 else None
    page_data = page_data if not is_error(page_data) else None
    return get_illust_parameters_from_artwork(artwork, page_data)


def get_illust_commentary(site_illust_id):
    artwork = get_illust_api_data(site_illust_id)
    if artwork is None:
        return None
    return get_artwork_commentary(artwork)


def get_artist_id_by_illust_id(site_illust_id):
    artwork = get_illust_api_data(site_illust_id)
    artist_id = safe_get(artwork, 'userId')
    return int(artist_id) if artist_id is not None else None


# #### Other

def print_auth():
    print("PHPSESSID:", PIXIV_PHPSESSID)
