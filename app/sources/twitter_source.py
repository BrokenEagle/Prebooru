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
from ..logical.utility import GetCurrentTime, GetFileExtension, GetHTTPFilename, SafeGet, DecodeJSON, FixupCRLF
from ..logical.file import LoadDefault, PutGetJSON
from ..database.error_db import CreateError, IsError
from ..database.cache_db import GetApiArtist, GetApiIllust, SaveApiData
from ..database.illust_db import GetSiteIllust
from ..config import WORKING_DIRECTORY, DATA_FILEPATH
from ..sites import Site, GetSiteDomain, GetSiteId


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

TOKEN_FILE = WORKING_DIRECTORY + DATA_FILEPATH + 'twittertoken.txt'


# ##FUNCTIONS

# Illust

def IllustHasImages(illust):
    return any(map(ImageUrlMapper, illust.urls))


def IllustHasVideos(illust):
    return any(map(VideoUrlMapper, illust.urls))


def PostHasImages(post):
    return any(map(ImageUrlMapper, post.illust_urls))


def PostHasVideos(post):
    return any(map(VideoUrlMapper, post.illust_urls))


def ImageIllustDownloadUrls(illust):
    return list(filter(lambda x: ImageUrlMapper, illust.urls))


def VideoIllustDownloadUrls(illust):
    video_illust_url = next(filter(VideoUrlMapper, illust.urls))
    thumb_illust_url = next(filter(ImageUrlMapper, illust.urls), None)
    return video_illust_url, thumb_illust_url


def VideoIllustVideoUrl(illust):
    return next(filter(VideoUrlMapper, illust.urls), None)


def VideoIllustThumbUrl(illust):
    return next(filter(ImageUrlMapper, illust.urls), None)


# Artist

def ArtistLinks(artist):
    return {
        'main': ArtistMainUrl(artist),
        'media': ArtistMediaUrl(artist),
        'likes': ArtistLikesUrl(artist),
    }


# Tag

def TagSearchUrl(tag):
    return TAG_SEARCH_HREFURL % tag.name


#   URL

def GetMediaExtension(media_url):
    match = IMAGE1_RG.match(media_url) or IMAGE2_RG.match(media_url)
    if match:
        return match.group(3)
    match = VIDEO1_RG.match(media_url)
    if match:
        return match.group(2)
    match = VIDEO2_RG.match(media_url)
    if match:
        return match.group(6)
    filename = GetHTTPFilename(media_url)
    return GetFileExtension(filename)


def ImageUrlMapper(x):
    return IsImageUrl(GetFullUrl(x))


def VideoUrlMapper(x):
    return IsVideoUrl(GetFullUrl(x))


def IsArtistUrl(url):
    return bool(USERS1_RG.match(url)) or IsArtistIdUrl(url)


def IsArtistIdUrl(url):
    return bool(USERS2_RG.match(url) or USERS3_RG.match(url))


def IsPostUrl(url):
    return bool(TWEET_RG.match(url))


def PartialMediaUrl(url):
    parse = urllib.parse.urlparse(url)
    site_id = GetSiteId(parse.netloc)
    match = IMAGE2_RG.match(url)
    query_addon = '?format=%s' % match.group(3) if match else ""
    return parse.path + query_addon if site_id != 0 else parse.geturl()


def IsMediaUrl(url):
    return IsImageUrl(url) or IsVideoUrl(url)


def IsImageUrl(url):
    return bool(IMAGE1_RG.match(url) or IMAGE2_RG.match(url) or IMAGE3_RG.match(url))


def IsVideoUrl(url):
    return bool(VIDEO1_RG.match(url) or VIDEO2_RG.match(url))


def IsRequestUrl(request_url):
    return IsPostUrl(request_url)


def GetUploadType(request_url):
    # Have already validated urls with UploadCheck
    return 'post' if IsPostUrl(request_url) else 'image'


def SiteId():
    return SITE_ID


def GetIllustId(request_url):
    return int(TWEET_RG.match(request_url).group(1))


def GetArtistIdUrlId(artist_url):
    match = USERS2_RG.match(artist_url) or USERS3_RG.match(artist_url)
    if match:
        return match.group(1)


def GetArtistId(artist_url):
    match = USERS2_RG.match(artist_url) or USERS3_RG.match(artist_url)
    if match:
        return match.group(1)
    match = USERS1_RG.match(artist_url)
    if match:
        screen_name = match.group(1)
        return GetTwitterUserID(screen_name)


def GetFullUrl(illust_url):
    media_url = GetMediaUrl(illust_url)
    if IMAGE1_RG.match(media_url):
        return media_url + ':orig'
    if IMAGE2_RG.match(media_url):
        return media_url + '&name=orig'
    return media_url


def SmallImageUrl(image_url):
    return NormalizedImageUrl(image_url) + ':small'


def NormalizedImageUrl(image_url):
    match = IMAGE1_RG.match(image_url) or IMAGE2_RG.match(image_url)
    if match:
        type, imagekey, extension, _ = match.groups()
        return IMAGE_SERVER + "/%s/%s.%s" % (type, imagekey, extension)
    match = IMAGE3_RG.match(image_url)
    type, imageid, path, imagekey, extension, _ = match.groups()
    path = path or ""
    return IMAGE_SERVER + "/%s/%s%s/img/%s.%s" % (type, imageid, path, imagekey, extension)


def GetMediaUrl(illust_url):
    return illust_url.url if illust_url.site_id == 0 else 'https://' + GetSiteDomain(illust_url.site_id) + illust_url.url


def GetPostUrl(illust):
    tweet_id = illust.site_illust_id
    if not HasArtistUrls(illust.artist):
        return GetIllustUrl(tweet_id)
    screen_name = ArtistScreenName(illust.artist)
    return "https://twitter.com/%s/status/%d" % (screen_name, tweet_id)


def GetIllustUrl(site_illust_id):
    return "https://twitter.com/i/web/status/%d" % site_illust_id


def SubscriptionCheck(request_url):
    artist_id = None
    artwork_match = USERS1_RG.match(request_url)
    if artwork_match:
        artist_id = int(artwork_match.group(1))
    return artist_id


def NormalizeImageURL(image_url):
    image_match = IMAGE1_RG.match(image_url) or IMAGE2_RG.match(image_url)
    return r'/media/%s.%s' % (image_match.group(2), image_match.group(3))


def HasArtistUrls(artist):
    return (artist.current_site_account is not None) or (len(artist.site_accounts) == 1)


def ArtistScreenName(artist):
    return artist.current_site_account if artist.current_site_account is not None else artist.site_accounts[0].name


def ArtistProfileUrls(artist):
    profile_urls = ['https://twitter.com/intent/user?user_id=%d' % artist.site_artist_id]
    for site_account in artist.site_accounts:
        profile_urls += ['https://twitter.com/%s' % site_account.name]
    return profile_urls


def ArtistBooruSearchUrl(artist):
    return 'http://twitter.com/intent/user?user_id=%d/' % artist.site_artist_id


def IllustCommentaries(illust):
    if len(illust.commentaries) == 0:
        return []
    commentary = illust.commentaries[0].body  # Twitter commentaries are unchangable.
    for tag in illust.tags:
        hashtag = '#' + tag.name
        hashtag_link = r'"%s":[https://twitter.com/hashtag/%s]' % (hashtag, tag.name)
        commentary = re.sub(r'%s(?=$|\s)' % hashtag, hashtag_link, commentary)
    return [commentary]


def ArtistMainUrl(artist):
    if not HasArtistUrls(artist):
        return ""
    screen_name = ArtistScreenName(artist)
    return 'https://twitter.com/%s' % screen_name


def ArtistMediaUrl(artist):
    url = ArtistMainUrl(artist)
    return url + '/media' if len(url) else ""


def ArtistLikesUrl(artist):
    url = ArtistMainUrl(artist)
    return url + '/likes' if len(url) else ""


def GetGlobalObjects(data, type_name):
    return SafeGet(data, 'globalObjects', type_name)


def GetGlobalObject(data, type_name, key):
    return SafeGet(data, 'globalObjects', type_name, key)


def ProcessTwitterTimestring(time_string):
    try:
        return datetime.datetime.strptime(time_string, '%a %b %d %H:%M:%S +0000 %Y')
    except ValueError:
        pass


def ConvertText(twitter_data, key, *subkeys):
    text = twitter_data[key]
    url_entries = SafeGet(twitter_data, 'entities', *subkeys) or []
    for url_entry in reversed(url_entries):
        replace_url = url_entry['expanded_url']
        start_index, end_index = url_entry['indices']
        text = text[:start_index] + replace_url + text[end_index:]
    return text


#   Database

def Prework(site_illust_id):
    illust = GetSiteIllust(site_illust_id, SITE_ID)
    if illust is not None:
        return
    twitter_data = GetTwitterIllustTimeline(site_illust_id)
    if IsError(twitter_data):
        return twitter_data
    tweets = []
    tweet_ids = set()
    for i in range(len(twitter_data)):
        tweet = SafeGet(twitter_data[i], 'result', 'legacy')
        if tweet is None or tweet['id_str'] in tweet_ids:
            continue
        tweets.append(tweet)
        tweet_ids.add(tweet['id_str'])
    SaveApiData(tweets, 'id_str', SITE_ID, 'illust')
    twusers = []
    user_ids = set()
    for i in range(len(twitter_data)):
        id_str = SafeGet(twitter_data[i], 'result', 'core', 'user', 'rest_id')
        user = SafeGet(twitter_data[i], 'result', 'core', 'user', 'legacy')
        if user is None or id_str in user_ids:
            continue
        user['id_str'] = id_str
        twusers.append(user)
        user_ids.add(id_str)
    SaveApiData(twusers, 'id_str', SITE_ID, 'artist')


# #### Token functions

def LoadGuestToken():
    global TOKEN_TIMESTAMP
    try:
        TOKEN_TIMESTAMP = os.path.getmtime(TOKEN_FILE) if os.path.exists(TOKEN_FILE) else None
        data = LoadDefault(TOKEN_FILE, {"token": None})
        return str(data['token']) if data['token'] is not None else None
    except Exception:
        return None


def SaveGuestToken(guest_token):
    PutGetJSON(TOKEN_FILE, 'w', {"token": str(guest_token)})


def CheckTokenFile():
    global TOKEN_TIMESTAMP
    last_timestamp = TOKEN_TIMESTAMP if 'TOKEN_TIMESTAMP' in globals() else None
    TOKEN_TIMESTAMP = os.path.getmtime(TOKEN_FILE) if os.path.exists(TOKEN_FILE) else None
    return last_timestamp == TOKEN_TIMESTAMP


# #### Network functions

def CheckGuestAuth(func):
    def wrapper(*args, **kwargs):
        if TWITTER_HEADERS is None or not CheckTokenFile():
            AuthenticateGuest()
        return func(*args, **kwargs)
    return wrapper


def AuthenticateGuest(override=False):
    global TWITTER_HEADERS
    TWITTER_HEADERS = {
        'authorization': 'Bearer %s' % TWITTER_GUEST_AUTH
    }
    guest_token = LoadGuestToken() if not override else None
    if guest_token is None:
        print("Authenticating as guest...")
        data = TwitterRequest('https://api.twitter.com/1.1/guest/activate.json', 'POST')
        guest_token = str(data['body']['guest_token'])
        SaveGuestToken(guest_token)
    else:
        print("Loaded guest token from file.")
    TWITTER_HEADERS['x-guest-token'] = guest_token


def ReauthenticationCheck(response):
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
        error_code = SafeGet(resp_json, 'errors', 0, 'code')
    elif type(resp_json['errors']) is str:
        error_json = DecodeJSON(resp_json['errors'])
        error_code = error_json and SafeGet(error_json, 'code')
    else:
        return False
    return error_code in [200, 239]


@CheckGuestAuth
def TwitterRequest(url, method='GET'):
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
        if not reauthenticated and ReauthenticationCheck(response):
            AuthenticateGuest(True)
            reauthenticated = True
        else:
            print("\n%s\nHTTP %d: %s (%s)" % (url, response.status_code, response.reason, response.text))
            return {'error': True, 'message': "HTTP %d - %s" % (response.status_code, response.reason)}
    try:
        data = response.json()
    except Exception:
        return {'error': True, 'message': "Error decoding response into JSON."}
    return {'error': False, 'body': data}


def GetGraphQLTimelineEntries(data, found_tweets):
    for key in data:
        if key == 'tweet_results':
            found_tweets.append(data[key])
        elif type(data[key]) is list:
            for i in range(len(data[key])):
                found_tweets = GetGraphQLTimelineEntries(data[key][i], found_tweets)
        elif type(data[key]) is dict:
            found_tweets = GetGraphQLTimelineEntries(data[key], found_tweets)
    return found_tweets


def GetTwitterIllustTimeline(illust_id):
    print("Getting twitter #%d" % illust_id)
    illust_id_str = str(illust_id)
    jsondata = TWITTER_ILLUST_TIMELINE_GRAPHQL.copy()
    jsondata['focalTweetId'] = illust_id_str
    urladdons = urllib.parse.urlencode({'variables': json.dumps(jsondata)})
    data = TwitterRequest("https://twitter.com/i/api/graphql/uvk82Jn4z84yUPI1rViRsg/TweetDetail?%s" % urladdons)
    if data['error']:
        return CreateError('sources.twitter.GetTwitterTimelineIllust', data['message'])
    found_tweets = GetGraphQLTimelineEntries(data['body'], [])
    if len(found_tweets) == 0:
        return CreateError('sources.twitter.GetTwitterTimelineIllust', "No tweets found in data.")
    tweet_ids = [SafeGet(tweet_entry, 'result', 'rest_id') for tweet_entry in found_tweets]
    if illust_id_str not in tweet_ids:
        return CreateError('sources.twitter.GetTwitterTimelineIllust', "Tweet not found: %d" % illust_id)
    return found_tweets


def GetTwitterIllust(illust_id):
    print("Getting twitter #%d" % illust_id)
    data = TwitterRequest('https://api.twitter.com/1.1/statuses/lookup.json?id=%d&trim_user=true&tweet_mode=extended&include_quote_count=true&include_reply_count=true' % illust_id)
    if data['error']:
        return CreateError('sources.twitter.GetTwitterIllust', data['message'])
    if len(data['body']) == 0:
        return CreateError('sources.twitter.GetTwitterIllust', "Tweet not found: %d" % illust_id)
    return data['body'][0]


def GetTwitterUserID(account):
    print("Getting user ID: %s" % account)
    jsondata = {
        'screen_name': account,
        'withHighlightedLabel': False
    }
    urladdons = urllib.parse.urlencode({'variables': json.dumps(jsondata)})
    data = TwitterRequest('https://twitter.com/i/api/graphql/Vf8si2dfZ1zmah8ePYPjDQ/UserByScreenNameWithoutResults?%s' % urladdons)
    if data['error']:
        return CreateError('sources.twitter.GetUserID', data['message'])
    return SafeGet(data, 'body', 'data', 'user', 'rest_id')


def GetTwitterArtist(artist_id):
    print("Getting user #%d" % artist_id)
    jsondata = {
        'userId': str(artist_id),
        'withHighlightedLabel': False,
    }
    urladdons = urllib.parse.urlencode({'variables': json.dumps(jsondata)})
    data = TwitterRequest('https://twitter.com/i/api/graphql/WN6Hck-Pwm-YP0uxVj1oMQ/UserByRestIdWithoutResults?%s' % urladdons)
    if data['error']:
        return CreateError('sources.twitter.GetTwitterArtist', data['message'])
    twitterdata = data['body']
    if 'errors' in twitterdata and len(twitterdata['errors']):
        return CreateError('sources.twitter.GetTwitterArtist', 'Twitter error: ' + '; '.join([error['message'] for error in twitterdata['errors']]))
    userdata = SafeGet(twitterdata, 'data', 'user')
    if userdata is None or 'rest_id' not in userdata or 'legacy' not in userdata:
        return CreateError('sources.twitter.GetTwitterArtist', "Error parsing data: %s" % json.dumps(twitterdata))
    retdata = userdata['legacy']
    retdata['id_str'] = userdata['rest_id']
    return retdata


# #### Param functions

# ###### ILLUST

def GetIllustCommentary(twitter_data):
    text = ConvertText(twitter_data, 'full_text', 'urls')
    return FixupCRLF(SHORT_URL_REPLACE_RG.sub('', text).strip())


def GetIllustTags(tweet):
    tag_data = SafeGet(tweet, 'entities', 'hashtags') or []
    return list(set(entry['text'].lower() for entry in tag_data))


def GetIllustUrlInfo(entry):
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
    site_id = GetSiteId(parse.netloc)
    url = parse.path + query_addon if site_id != 0 else parse.geturl()
    return url, site_id, dimensions


def GetIllustUrls(tweet):
    return GetImageUrls(tweet) + GetVideoUrls(tweet)


def GetImageUrls(tweet):
    illust_urls = []
    image_url_data = SafeGet(tweet, 'entities', 'media') or []
    for i in range(len(image_url_data)):
        url, site_id, dimensions = GetIllustUrlInfo(image_url_data[i])
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


def GetVideoUrls(tweet):
    url_data = SafeGet(tweet, 'extended_entities', 'media') or []
    video_url_data = [url_entry for url_entry in url_data if url_entry['type'] in ['animated_gif', 'video']]
    if len(video_url_data) == 0:
        return []
    url, site_id, dimensions = GetIllustUrlInfo(video_url_data[0])
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


def GetIllustParametersFromTweet(tweet):
    site_artist_id = SafeGet(tweet, 'user', 'id_str') or SafeGet(tweet, 'user_id_str')
    return {
        'site_id': SITE_ID,
        'site_illust_id': int(tweet['id_str']),
        'site_created': ProcessTwitterTimestring(tweet['created_at']),
        'pages': len(tweet['extended_entities']['media']),
        'score': tweet['favorite_count'],
        'retweets': tweet['retweet_count'],
        'replies': tweet['reply_count'] if 'reply_count' in tweet else None,
        'quotes': tweet['quote_count'] if 'quote_count' in tweet else None,
        'requery': GetCurrentTime() + datetime.timedelta(days=1),
        'tags': GetIllustTags(tweet),
        'commentaries': GetIllustCommentary(tweet) or None,
        'illust_urls': GetIllustUrls(tweet),
        'active': True,
        'site_artist_id': int(site_artist_id) if site_artist_id is not None else None,
    }


# ###### ARTIST

def GetArtistProfile(twitter_data):
    return FixupCRLF(ConvertText(twitter_data, 'description', 'description', 'urls'))


def GetTwitterUserWebpages(twuser):
    webpages = set()
    url_entries = SafeGet(twuser, 'entities', 'url', 'urls') or []
    for entry in url_entries:
        if 'expanded_url' in entry:
            webpages.add(entry['expanded_url'])
        elif 'url' in entry:
            webpages.add(entry['url'])
    url_entries = SafeGet(twuser, 'entities', 'description', 'urls') or []
    for entry in url_entries:
        if 'expanded_url' in entry:
            webpages.add(entry['expanded_url'])
        elif 'url' in entry:
            webpages.add(entry['url'])
    return list(webpages)


def GetArtistParametersFromTwuser(twuser):
    return {
        'site_id': SITE_ID,
        'site_artist_id': int(twuser['id_str']),
        'site_created': ProcessTwitterTimestring(twuser['created_at']),
        'current_site_account': twuser['screen_name'],
        'requery': GetCurrentTime() + datetime.timedelta(days=1),
        'active': True,
        'names': [twuser['name']],
        'site_accounts': [twuser['screen_name']],
        'profiles': GetArtistProfile(twuser) or None,
        'webpages': GetTwitterUserWebpages(twuser),
    }


# #### Data lookup functions

def GetArtistApiData(site_artist_id):
    twuser = GetApiArtist(site_artist_id, SITE_ID)
    if twuser is None:
        twuser = GetTwitterArtist(site_artist_id)
        if IsError(twuser):
            return
        SaveApiData([twuser], 'id_str', SITE_ID, 'artist')
    return twuser


def GetArtistData(site_artist_id):
    twuser = GetArtistApiData(site_artist_id)
    if twuser is None:
        return {'active': False, 'requery': None}
    return GetArtistParametersFromTwuser(twuser)


def GetIllustApiData(site_illust_id):
    tweet = GetApiIllust(site_illust_id, SITE_ID)
    if tweet is None:
        tweet = GetTwitterIllust(site_illust_id)
        if IsError(tweet):
            return
        SaveApiData([tweet], 'id_str', SITE_ID, 'illust')
    return tweet


def GetIllustData(site_illust_id):
    tweet = GetIllustApiData(site_illust_id)
    if tweet is None:
        return {'active': False, 'requery': None}
    return GetIllustParametersFromTweet(tweet)


def GetArtistIdByIllustId(site_illust_id):
    tweet = GetIllustApiData(site_illust_id)
    return SafeGet(tweet, 'user', 'id_str')
