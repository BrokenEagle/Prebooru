# APP/SOURCES/TWITTER.PY

# ##PYTHON IMPORTS
import os
import re
import time
import json
import urllib
import requests
import datetime

# ##LOCAL IMPORTS
from ..utility import get_current_time, get_file_extension, get_http_filename, safe_get, decode_json, fixup_crlf
from ..file import load_default, put_get_json
from ...database.error_db import create_error, is_error
from ...database.cache_db import get_api_artist, get_api_illust, save_api_data
from ...database.illust_db import get_site_illust
from ...config import DATA_DIRECTORY
from ..sites import Site, get_site_domain, get_site_id


# ##GLOBAL VARIABLES

# #### Module variables

NAME = 'twitter'

IMAGE_HEADERS = {}

BAD_ID_TAGS = ['bad_id', 'bad_twitter_id']

ILLUST_SHORTLINK = 'twitter #%d'
ARTIST_SHORTLINK = 'twuser #%d'

ILLUST_HREFURL = 'https://twitter.com/i/web/status/%d'
ARTIST_HREFURL = 'https://twitter.com/i/user/%d'
TAG_SEARCH_HREFURL = 'https://twitter.com/hashtag/%s'

SITE_ID = Site.TWITTER.value

HAS_TAG_SEARCH = True

TWITTER_HEADERS = None


# #### Regex variables

TWEET_RG = re.compile(r"""
^https?://twitter\.com                  # Hostname
/[\w-]+                                 # Account
/status
/(\d+)                                  # ID
(\?|$)                                  # End
""", re.X | re.IGNORECASE)

"""https://twitter.com/danboorubot"""

USERS1_RG = re.compile(r"""
^https?://twitter\.com                  # Hostname
/([\w-]+)                               # Account
(\?|$)                                  # End
""", re.X | re.IGNORECASE)

"""https://twitter.com/intent/user?user_id=2807221321"""

USERS2_RG = re.compile(r"""
^https?://twitter\.com                  # Hostname
/intent/user\?user_id=
(\d+)                                   # User ID
$                                       # End
""", re.X | re.IGNORECASE)

"""https://twitter.com/i/user/994169624659804161"""

USERS3_RG = re.compile(r"""
^https?://twitter\.com                  # Hostname
/i/user
/(\d+)                                  # User ID
(\?|$)                                  # End
""", re.X | re.IGNORECASE)

"""https://pbs.twimg.com/media/Es5NR-YVgAQzpJP.jpg:orig"""
"""http://pbs.twimg.com/tweet_video_thumb/EiWHH0HVgAAbEcF.jpg"""

IMAGE1_RG = re.compile(r"""
^https?://pbs\.twimg\.com               # Hostname
/(media|tweet_video_thumb)
/([^.]+)                               # Image key
\.(jpg|png|gif)                         # Extension
(?::(orig|large|medium|small|thumb))?   # Size
""", re.X | re.IGNORECASE)

"""https://pbs.twimg.com/media/Es5NR-YVgAQzpJP?format=jpg&name=900x900"""

IMAGE2_RG = re.compile(r"""
^https?://pbs\.twimg\.com               # Hostname
/(media|tweet_video_thumb)
/([\w-]+)                               # Image key
\?format=(jpg|png|gif)                  # Extension
(?:&name=(\w+))?$                       # Size
""", re.X | re.IGNORECASE)

"""http://pbs.twimg.com/ext_tw_video_thumb/1270031579470061568/pu/img/cLxRLtYjq_D10ome.jpg"""
"""https://pbs.twimg.com/amplify_video_thumb/1096312943845593088/img/VE7v_9MVr3tqZMNH.jpg"""

IMAGE3_RG = re.compile(r"""
^https?://pbs\.twimg\.com                   # Hostname
/(ext_tw_video_thumb|amplify_video_thumb)   # Type
/(\d+)                                      # Twitter ID
(/\w+)?                                     # Path
/img
/([^.]+)                                    # Image key
\.(jpg|png|gif)                             # Extension
(?::(orig|large|medium|small|thumb))?       # Size
""", re.X | re.IGNORECASE)

"""https://pbs.twimg.com/ext_tw_video_thumb/1440389658647490560/pu/img/tZehLN5THk3Yyedt?format=jpg&name=orig"""

IMAGE4_RG = re.compile(r"""
^https?://pbs\.twimg\.com                   # Hostname
/(ext_tw_video_thumb|amplify_video_thumb)   # Type
/(\d+)                                      # Twitter ID
(/\w+)?                                     # Path
/img
/([^.]+)                                    # Image key
\?format=(jpg|png|gif)                      # Extension
(?:&name=(\w+))?$                           # Size
""", re.X | re.IGNORECASE)


"""https://video.twimg.com/tweet_video/EiWHH0HVgAAbEcF.mp4"""

VIDEO1_RG = re.compile(r"""
https?://video\.twimg\.com              # Hostname
/tweet_video
/([^.]+)                                  # Video key
\.(mp4)                                 # Extension
""", re.X | re.IGNORECASE)


"""https://video.twimg.com/ext_tw_video/1270031579470061568/pu/vid/640x640/M54mOuT519Rb5eXs.mp4"""
"""https://video.twimg.com/amplify_video/1296680886113456134/vid/1136x640/7_ps073yayavGQUe.mp4"""

VIDEO2_RG = re.compile(r"""
https?://video\.twimg\.com              # Hostname
/(ext_tw_video|amplify_video)           # Type
/(\d+)                                  # Twitter ID
(?:/\w+)?
/vid
/(\d+)x(\d+)                            # Dimensions
/([^.]+)                               # Video key
\.(mp4)                                 # Extension
""", re.X | re.IGNORECASE)

SHORT_URL_REPLACE_RG = re.compile(r"""
https?://t\.co                         # Hostname
/ [\w-]+                               # Account
""", re.X | re.IGNORECASE)


# #### Network variables

REQUEST_METHODS = {
    'GET': requests.get,
    'POST': requests.post
}

TWITTER_GUEST_AUTH = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

TWITTER_SEARCH_PARAMS = {
    "tweet_search_mode": "live",
    "query_source": "typed_query",
    "pc": "1",
    "spelling_corrections": "1",
}

TWITTER_ILLUST_TIMELINE_GRAPHQL = {
    "includePromotedContent": True,
    "withHighlightedLabel": True,
    "withCommunity": False,
    "withTweetQuoteCount": True,
    "withBirdwatchNotes": False,
    "withBirdwatchPivots": False,
    "withTweetResult": True,
    "withReactions": False,
    "withSuperFollowsTweetFields": False,
    "withSuperFollowsUserFields": False,
    "withUserResults": False,
    "withVoice": True
}

# #### Other variables

IMAGE_SERVER = 'https://pbs.twimg.com'
TWITTER_SIZES = [':orig', ':large', ':medium', ':small']

TOKEN_FILE = os.path.join(DATA_DIRECTORY, 'twittertoken.txt')


# ##FUNCTIONS

# Illust

def illust_has_images(illust):
    return any(map(image_url_mapper, illust.urls))


def illust_has_videos(illust):
    return any(map(video_url_mapper, illust.urls))


def image_illust_download_urls(illust):
    return list(filter(lambda x: image_url_mapper, illust.urls))


def VideoIllustDownloadUrls(illust):
    video_illust_url = next(filter(video_url_mapper, illust.urls))
    thumb_illust_url = next(filter(image_url_mapper, illust.urls), None)
    return video_illust_url, thumb_illust_url


def video_illust_video_url(illust):
    return next(filter(video_url_mapper, illust.urls), None)


def video_illust_thumb_url(illust):
    return next(filter(image_url_mapper, illust.urls), None)


# Artist

def artist_links(artist):
    return {
        'main': artist_main_url(artist),
        'media': artist_media_url(artist),
        'likes': artist_likes_url(artist),
    }


# Tag

def tag_search_url(tag):
    return TAG_SEARCH_HREFURL % tag.name


#   URL

def get_media_extension(media_url):
    match = IMAGE1_RG.match(media_url) or IMAGE2_RG.match(media_url)
    if match:
        return match.group(3)
    match = VIDEO1_RG.match(media_url)
    if match:
        return match.group(2)
    match = VIDEO2_RG.match(media_url)
    if match:
        return match.group(6)
    filename = get_http_filename(media_url)
    return get_file_extension(filename)


def image_url_mapper(x):
    return is_image_url(get_full_url(x))


def video_url_mapper(x):
    return is_video_url(get_full_url(x))


def is_artist_url(url):
    return bool(USERS1_RG.match(url)) or is_artist_id_url(url)


def is_artist_id_url(url):
    return bool(USERS2_RG.match(url) or USERS3_RG.match(url))


def is_post_url(url):
    return bool(TWEET_RG.match(url))


def partial_media_url(url):
    parse = urllib.parse.urlparse(url)
    site_id = get_site_id(parse.netloc)
    match = IMAGE2_RG.match(url)
    query_addon = '?format=%s' % match.group(3) if match else ""
    return parse.path + query_addon if site_id != 0 else parse.geturl()


def is_image_url(url):
    return bool(IMAGE1_RG.match(url) or IMAGE2_RG.match(url) or IMAGE3_RG.match(url) or IMAGE4_RG.match(url))


def is_video_url(url):
    return bool(VIDEO1_RG.match(url) or VIDEO2_RG.match(url))


def is_request_url(request_url):
    return is_post_url(request_url)


def get_illust_id(request_url):
    return int(TWEET_RG.match(request_url).group(1))


def get_artist_id_url_id(artist_url):
    match = USERS2_RG.match(artist_url) or USERS3_RG.match(artist_url)
    if match:
        return match.group(1)


def get_artist_id(artist_url):
    match = USERS2_RG.match(artist_url) or USERS3_RG.match(artist_url)
    if match:
        return match.group(1)
    match = USERS1_RG.match(artist_url)
    if match:
        screen_name = match.group(1)
        return get_twitter_user_id(screen_name)


def get_full_url(illust_url):
    media_url = get_media_url(illust_url)
    if IMAGE1_RG.match(media_url):
        return media_url + ':orig'
    if IMAGE2_RG.match(media_url):
        return media_url + '&name=orig'
    return media_url


def small_image_url(image_url):
    return normalized_image_url(image_url) + ':small'


def normalized_image_url(image_url):
    match = IMAGE1_RG.match(image_url) or IMAGE2_RG.match(image_url)
    if match:
        type, imagekey, extension, _ = match.groups()
        return IMAGE_SERVER + "/%s/%s.%s" % (type, imagekey, extension)
    match = IMAGE3_RG.match(image_url) or IMAGE4_RG.match(image_url)
    type, imageid, path, imagekey, extension, _ = match.groups()
    path = path or ""
    return IMAGE_SERVER + "/%s/%s%s/img/%s.%s" % (type, imageid, path, imagekey, extension)


def get_media_url(illust_url):
    return illust_url.url if illust_url.site_id == 0 else 'https://' + get_site_domain(illust_url.site_id) + illust_url.url


def get_post_url(illust):
    tweet_id = illust.site_illust_id
    if not has_artist_urls(illust.artist):
        return get_illust_url(tweet_id)
    screen_name = artist_screen_name(illust.artist)
    return "https://twitter.com/%s/status/%d" % (screen_name, tweet_id)


def get_illust_url(site_illust_id):
    return "https://twitter.com/i/web/status/%d" % site_illust_id


def normalize_image_url(image_url):
    image_match = IMAGE1_RG.match(image_url) or IMAGE2_RG.match(image_url)
    return r'/media/%s.%s' % (image_match.group(2), image_match.group(3))


def has_artist_urls(artist):
    return (artist.current_site_account is not None) or (len(artist.site_accounts) == 1)


def artist_screen_name(artist):
    return artist.current_site_account if artist.current_site_account is not None else artist.site_accounts[0].name


def artist_profile_urls(artist):
    profile_urls = ['https://twitter.com/intent/user?user_id=%d' % artist.site_artist_id]
    for site_account in artist.site_accounts:
        profile_urls += ['https://twitter.com/%s' % site_account.name]
    return profile_urls


def artist_booru_search_url(artist):
    return 'http://twitter.com/intent/user?user_id=%d/' % artist.site_artist_id


def illust_commentaries_dtext(illust):
    if len(illust.commentaries) == 0:
        return []
    commentary = illust.commentaries[0].body  # Twitter commentaries are unchangable.
    for tag in illust.tags:
        hashtag = '#' + tag.name
        hashtag_link = r'"%s":[https://twitter.com/hashtag/%s]' % (hashtag, tag.name)
        commentary = re.sub(r'%s(?=$|\s)' % hashtag, hashtag_link, commentary)
    return [commentary]


def artist_main_url(artist):
    if not has_artist_urls(artist):
        return ""
    screen_name = artist_screen_name(artist)
    return 'https://twitter.com/%s' % screen_name


def artist_media_url(artist):
    url = artist_main_url(artist)
    return url + '/media' if len(url) else ""


def artist_likes_url(artist):
    url = artist_main_url(artist)
    return url + '/likes' if len(url) else ""


def process_twitter_timestring(time_string):
    try:
        return datetime.datetime.strptime(time_string, '%a %b %d %H:%M:%S +0000 %Y')
    except ValueError:
        pass


def convert_entity_text(twitter_data, key, *subkeys):
    text = twitter_data[key]
    url_entries = safe_get(twitter_data, 'entities', *subkeys) or []
    for url_entry in reversed(url_entries):
        replace_url = url_entry['expanded_url']
        start_index, end_index = url_entry['indices']
        text = text[:start_index] + replace_url + text[end_index:]
    return text


#   Database

def source_prework(site_illust_id):
    illust = get_site_illust(site_illust_id, SITE_ID)
    if illust is not None:
        return
    twitter_data = get_twitter_illust_timeline(site_illust_id)
    if is_error(twitter_data):
        return twitter_data
    tweets = []
    tweet_ids = set()
    for i in range(len(twitter_data)):
        tweet = safe_get(twitter_data[i], 'result', 'legacy')
        if tweet is None or tweet['id_str'] in tweet_ids:
            continue
        tweets.append(tweet)
        tweet_ids.add(tweet['id_str'])
    save_api_data(tweets, 'id_str', SITE_ID, 'illust')
    twusers = []
    user_ids = set()
    for i in range(len(twitter_data)):
        id_str = safe_get(twitter_data[i], 'result', 'core', 'user', 'rest_id')
        user = safe_get(twitter_data[i], 'result', 'core', 'user', 'legacy')
        if user is None or id_str in user_ids:
            continue
        user['id_str'] = id_str
        twusers.append(user)
        user_ids.add(id_str)
    save_api_data(twusers, 'id_str', SITE_ID, 'artist')


# #### Token functions

def load_guest_token():
    global TOKEN_TIMESTAMP
    try:
        TOKEN_TIMESTAMP = os.path.getmtime(TOKEN_FILE) if os.path.exists(TOKEN_FILE) else None
        data = load_default(TOKEN_FILE, {"token": None})
        return str(data['token']) if data['token'] is not None else None
    except Exception:
        return None


def save_guest_token(guest_token):
    put_get_json(TOKEN_FILE, 'w', {"token": str(guest_token)})


def check_token_file():
    global TOKEN_TIMESTAMP
    last_timestamp = TOKEN_TIMESTAMP if 'TOKEN_TIMESTAMP' in globals() else None
    TOKEN_TIMESTAMP = os.path.getmtime(TOKEN_FILE) if os.path.exists(TOKEN_FILE) else None
    return last_timestamp == TOKEN_TIMESTAMP


# #### Network functions

def check_guest_auth(func):
    def wrapper(*args, **kwargs):
        if TWITTER_HEADERS is None or not check_token_file():
            authenticate_guest()
        return func(*args, **kwargs)
    return wrapper


def authenticate_guest(override=False):
    global TWITTER_HEADERS
    TWITTER_HEADERS = {
        'authorization': 'Bearer %s' % TWITTER_GUEST_AUTH
    }
    guest_token = load_guest_token() if not override else None
    if guest_token is None:
        print("Authenticating as guest...")
        data = twitter_request('https://api.twitter.com/1.1/guest/activate.json', 'POST')
        guest_token = str(data['body']['guest_token'])
        save_guest_token(guest_token)
    else:
        print("Loaded guest token from file.")
    TWITTER_HEADERS['x-guest-token'] = guest_token


def reauthentication_check(response):
    if response.status_code == 401:
        return True
    if response.status_code != 403:
        return False
    try:
        resp_json = response.json()
    except Exception:
        return False
    if 'errors' not in resp_json:
        return False
    if type(resp_json['errors']) is list:
        error_code = safe_get(resp_json, 'errors', 0, 'code')
    elif type(resp_json['errors']) is str:
        error_json = decode_json(resp_json['errors'])
        error_code = error_json and safe_get(error_json, 'code')
    else:
        return False
    return error_code in [200, 239]


@check_guest_auth
def twitter_request(url, method='GET'):
    reauthenticated = False
    for i in range(3):
        try:
            response = REQUEST_METHODS[method](url, headers=TWITTER_HEADERS, timeout=10)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            if i == 2:
                print("Connection errors exceeded!")
                return {'error': True, 'message': repr(e)}
            print("Pausing for network timeout...")
            time.sleep(5)
            continue
        if response.status_code == 200:
            break
        if not reauthenticated and reauthentication_check(response):
            authenticate_guest(True)
            reauthenticated = True
        else:
            print("\n%s\nHTTP %d: %s (%s)" % (url, response.status_code, response.reason, response.text))
            return {'error': True, 'message': "HTTP %d - %s" % (response.status_code, response.reason)}
    try:
        data = response.json()
    except Exception:
        return {'error': True, 'message': "Error decoding response into JSON."}
    return {'error': False, 'body': data}


def get_graphql_timeline_entries(data, found_tweets):
    for key in data:
        if key == 'tweet_results':
            found_tweets.append(data[key])
        elif type(data[key]) is list:
            for i in range(len(data[key])):
                found_tweets = get_graphql_timeline_entries(data[key][i], found_tweets)
        elif type(data[key]) is dict:
            found_tweets = get_graphql_timeline_entries(data[key], found_tweets)
    return found_tweets


def get_twitter_illust_timeline(illust_id):
    print("Getting twitter #%d" % illust_id)
    illust_id_str = str(illust_id)
    jsondata = TWITTER_ILLUST_TIMELINE_GRAPHQL.copy()
    jsondata['focalTweetId'] = illust_id_str
    urladdons = urllib.parse.urlencode({'variables': json.dumps(jsondata)})
    data = twitter_request("https://twitter.com/i/api/graphql/uvk82Jn4z84yUPI1rViRsg/TweetDetail?%s" % urladdons)
    if data['error']:
        return create_error('logical.sources.twitter.GetTwitterTimelineIllust', data['message'])
    found_tweets = get_graphql_timeline_entries(data['body'], [])
    if len(found_tweets) == 0:
        return create_error('logical.sources.twitter.GetTwitterTimelineIllust', "No tweets found in data.")
    tweet_ids = [safe_get(tweet_entry, 'result', 'rest_id') for tweet_entry in found_tweets]
    if illust_id_str not in tweet_ids:
        return create_error('logical.sources.twitter.GetTwitterTimelineIllust', "Tweet not found: %d" % illust_id)
    return found_tweets


def get_twitter_illust(illust_id):
    print("Getting twitter #%d" % illust_id)
    data = twitter_request('https://api.twitter.com/1.1/statuses/lookup.json?id=%d&trim_user=true&tweet_mode=extended&include_quote_count=true&include_reply_count=true' % illust_id)
    if data['error']:
        return create_error('logical.sources.twitter.get_twitter_illust', data['message'])
    if len(data['body']) == 0:
        return create_error('logical.sources.twitter.get_twitter_illust', "Tweet not found: %d" % illust_id)
    return data['body'][0]


def get_twitter_user_id(account):
    print("Getting user ID: %s" % account)
    jsondata = {
        'screen_name': account,
        'withHighlightedLabel': False
    }
    urladdons = urllib.parse.urlencode({'variables': json.dumps(jsondata)})
    data = twitter_request('https://twitter.com/i/api/graphql/Vf8si2dfZ1zmah8ePYPjDQ/UserByScreenNameWithoutResults?%s' % urladdons)
    if data['error']:
        return create_error('logical.sources.twitter.GetUserID', data['message'])
    return safe_get(data, 'body', 'data', 'user', 'rest_id')


def get_twitter_artist(artist_id):
    print("Getting user #%d" % artist_id)
    jsondata = {
        'userId': str(artist_id),
        'withHighlightedLabel': False,
    }
    urladdons = urllib.parse.urlencode({'variables': json.dumps(jsondata)})
    data = twitter_request('https://twitter.com/i/api/graphql/WN6Hck-Pwm-YP0uxVj1oMQ/UserByRestIdWithoutResults?%s' % urladdons)
    if data['error']:
        return create_error('logical.sources.twitter.get_twitter_artist', data['message'])
    twitterdata = data['body']
    if 'errors' in twitterdata and len(twitterdata['errors']):
        return create_error('logical.sources.twitter.get_twitter_artist', 'Twitter error: ' + '; '.join([error['message'] for error in twitterdata['errors']]))
    userdata = safe_get(twitterdata, 'data', 'user')
    if userdata is None or 'rest_id' not in userdata or 'legacy' not in userdata:
        return create_error('logical.sources.twitter.get_twitter_artist', "Error parsing data: %s" % json.dumps(twitterdata))
    retdata = userdata['legacy']
    retdata['id_str'] = userdata['rest_id']
    return retdata


# #### Param functions

# ###### ILLUST

def get_tweet_commentary(twitter_data):
    text = convert_entity_text(twitter_data, 'full_text', 'urls')
    return fixup_crlf(SHORT_URL_REPLACE_RG.sub('', text).strip())


def get_illust_tags(tweet):
    tag_data = safe_get(tweet, 'entities', 'hashtags') or []
    return list(set(entry['text'].lower() for entry in tag_data))


def get_illust_url_info(entry):
    query_addon = ""
    if entry['type'] == 'photo':
        parse = urllib.parse.urlparse(entry['media_url_https'])
        dimensions = (entry['original_info']['width'], entry['original_info']['height'])
        match = IMAGE2_RG.match(entry['media_url_https'])
        if match:
            query_addon = '?format=%s' % match.group(3)
    elif entry['type'] == 'video' or entry['type'] == 'animated_gif':
        variants = entry['video_info']['variants']
        valid_variants = [variant for variant in variants if 'bitrate' in variant]
        max_bitrate = max(map(lambda x: x['bitrate'], valid_variants))
        max_video = next(filter(lambda x: x['bitrate'] == max_bitrate, valid_variants))
        parse = urllib.parse.urlparse(max_video['url'])
        dimensions = (entry['sizes']['large']['w'], entry['sizes']['large']['h'])
    else:
        return None, None, None
    site_id = get_site_id(parse.netloc)
    url = parse.path + query_addon if site_id != 0 else parse.geturl()
    return url, site_id, dimensions


def get_tweet_illust_urls(tweet):
    return get_tweet_image_urls(tweet) + get_tweet_video_urls(tweet)


def get_tweet_image_urls(tweet):
    illust_urls = []
    image_url_data = safe_get(tweet, 'entities', 'media') or []
    for i in range(len(image_url_data)):
        url, site_id, dimensions = get_illust_url_info(image_url_data[i])
        if url is None:
            continue
        illust_urls.append({
            'site_id': site_id,
            'url': url,
            'width': dimensions[0],
            'height': dimensions[1],
            'order': i + 1,
            'active': True,
        })
    return illust_urls


def get_tweet_video_urls(tweet):
    url_data = safe_get(tweet, 'extended_entities', 'media') or []
    video_url_data = [url_entry for url_entry in url_data if url_entry['type'] in ['animated_gif', 'video']]
    if len(video_url_data) == 0:
        return []
    url, site_id, dimensions = get_illust_url_info(video_url_data[0])
    if url is None:
        return []
    return [{
        'site_id': site_id,
        'url': url,
        'width': dimensions[0],
        'height': dimensions[1],
        'order': 1,
        'active': True,
    }]


def get_illust_parameters_from_tweet(tweet):
    site_artist_id = safe_get(tweet, 'user', 'id_str') or safe_get(tweet, 'user_id_str')
    return {
        'site_id': SITE_ID,
        'site_illust_id': int(tweet['id_str']),
        'site_created': process_twitter_timestring(tweet['created_at']),
        'pages': len(tweet['extended_entities']['media']),
        'score': tweet['favorite_count'],
        'retweets': tweet['retweet_count'],
        'replies': tweet['reply_count'] if 'reply_count' in tweet else None,
        'quotes': tweet['quote_count'] if 'quote_count' in tweet else None,
        'requery': get_current_time() + datetime.timedelta(days=1),
        'tags': get_illust_tags(tweet),
        'commentaries': get_tweet_commentary(tweet) or None,
        'illust_urls': get_tweet_illust_urls(tweet),
        'active': True,
        'site_artist_id': int(site_artist_id) if site_artist_id is not None else None,
    }


# ###### ARTIST

def get_twuser_profile(twitter_data):
    return fixup_crlf(convert_entity_text(twitter_data, 'description', 'description', 'urls'))


def get_twuser_webpages(twuser):
    webpages = set()
    url_entries = safe_get(twuser, 'entities', 'url', 'urls') or []
    for entry in url_entries:
        if 'expanded_url' in entry:
            webpages.add(entry['expanded_url'])
        elif 'url' in entry:
            webpages.add(entry['url'])
    url_entries = safe_get(twuser, 'entities', 'description', 'urls') or []
    for entry in url_entries:
        if 'expanded_url' in entry:
            webpages.add(entry['expanded_url'])
        elif 'url' in entry:
            webpages.add(entry['url'])
    return list(webpages)


def get_artist_parameters_from_twuser(twuser):
    return {
        'site_id': SITE_ID,
        'site_artist_id': int(twuser['id_str']),
        'site_created': process_twitter_timestring(twuser['created_at']),
        'current_site_account': twuser['screen_name'],
        'requery': get_current_time() + datetime.timedelta(days=1),
        'active': True,
        'names': [twuser['name']],
        'site_accounts': [twuser['screen_name']],
        'profiles': get_twuser_profile(twuser) or None,
        'webpages': get_twuser_webpages(twuser),
    }


# #### Data lookup functions

def get_artist_api_data(site_artist_id):
    twuser = get_api_artist(site_artist_id, SITE_ID)
    if twuser is None:
        twuser = get_twitter_artist(site_artist_id)
        if is_error(twuser):
            return
        save_api_data([twuser], 'id_str', SITE_ID, 'artist')
    return twuser


def get_artist_data(site_artist_id):
    twuser = get_artist_api_data(site_artist_id)
    if twuser is None:
        return {'active': False, 'requery': None}
    return get_artist_parameters_from_twuser(twuser)


def get_illust_api_data(site_illust_id):
    tweet = get_api_illust(site_illust_id, SITE_ID)
    if tweet is None:
        tweet = get_twitter_illust(site_illust_id)
        if is_error(tweet):
            return
        save_api_data([tweet], 'id_str', SITE_ID, 'illust')
    return tweet


def get_illust_data(site_illust_id):
    tweet = get_illust_api_data(site_illust_id)
    if tweet is None:
        return {'active': False, 'requery': None}
    return get_illust_parameters_from_tweet(tweet)


def get_artist_id_by_illust_id(site_illust_id):
    tweet = get_illust_api_data(site_illust_id)
    return safe_get(tweet, 'user', 'id_str')