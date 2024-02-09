# APP/LOGICAL/SOURCES/TWITTER_SRC.PY

# ## PYTHON IMPORTS
import os
import re
import sys
import time
import json
import html
import urllib
import datetime

# ## EXTERNAL IMPORTS
import requests
import httpx
from wtforms import RadioField, BooleanField, IntegerField, TextField

# ## PACKAGE IMPORTS
from config import DATA_DIRECTORY, DEBUG_MODE, TWITTER_USER_TOKEN, TWITTER_CSRF_TOKEN
from utility.data import safe_get, decode_json, fixup_crlf, safe_check
from utility.time import get_current_time, datetime_from_epoch
from utility.file import get_file_extension, get_http_filename, load_default, put_get_json
from utility.uprint import print_info, print_warning, print_error

# ## LOCAL IMPORTS
from ...enum_imports import site_descriptor, api_data_type
from ..logger import log_network_error
from ..database.error_db import create_error, is_error
from ..database.api_data_db import get_api_artist, get_api_illust, save_api_data
from ..database.artist_db import inactivate_artist
from ..database.illust_db import get_site_illust
from ..database.server_info_db import get_next_wait, update_next_wait
from ..database.jobs_db import get_job_status_data, update_job_status
from ..records.artist_rec import update_artist


# ## GLOBAL VARIABLES

# #### Module variables

SELF = sys.modules[__name__]

IMAGE_HEADERS = {}

BAD_ID_TAGS = ['bad_id', 'bad_twitter_id']

ILLUST_SHORTLINK = 'twitter #%d'
ARTIST_SHORTLINK = 'twuser #%d'

ILLUST_HREFURL = 'https://twitter.com/i/web/status/%d'
ARTIST_HREFURL = 'https://twitter.com/i/user/%d'
TAG_SEARCH_HREFURL = 'https://twitter.com/hashtag/%s?src=hashtag_click&f=live'

SITE = site_descriptor.twitter

HAS_TAG_SEARCH = True


# #### Regex variables

# ###### Hostname regexes

TWITTER_HOST_RG = re.compile(r'^https?://twitter\.com', re.IGNORECASE)
TWIMG_HOST_RG = re.compile(r'^https?://pbs\.twimg\.com', re.IGNORECASE)
TWVIDEO_HOST_RG = re.compile(r'^https?://video\.twimg\.com', re.IGNORECASE)

# ###### Partial URL regexes

TWEET1_PARTIAL_RG = re.compile(r"""
/[\w-]+                                 # Account
/status
/(\d+)                                  # ID
(\?|$)                                  # End
""", re.X | re.IGNORECASE)

TWEET2_PARTIAL_RG = re.compile(r"""
/i/web/status
/(\d+)                                  # ID
(\?|$)                                  # End
""", re.X | re.IGNORECASE)

USERS1_PARTIAL_RG = re.compile(r"""
/([\w-]+)                               # Account
(\?|$)                                  # End
""", re.X | re.IGNORECASE)

USERS2_PARTIAL_RG = re.compile(r"""
/intent/user\?user_id=
(\d+)                                   # User ID
$                                       # End
""", re.X | re.IGNORECASE)

USERS3_PARTIAL_RG = re.compile(r"""
/i/user
/(\d+)                                  # User ID
(\?|$)                                  # End
""", re.X | re.IGNORECASE)

IMAGE1_PARTIAL_RG = re.compile(r"""
/(media|tweet_video_thumb)
/([^.]+)                               # Image key
\.(jpg|png|gif)                         # Extension
(?::(orig|large|medium|small|thumb))?   # Size
""", re.X | re.IGNORECASE)

IMAGE2_PARTIAL_RG = re.compile(r"""
/(media|tweet_video_thumb)
/([\w-]+)                               # Image key
\?format=(jpg|png|gif)                  # Extension
(?:&name=(\w+))?$                       # Size
""", re.X | re.IGNORECASE)

IMAGE3_PARTIAL_RG = re.compile(r"""
/(ext_tw_video_thumb|amplify_video_thumb)   # Type
/(\d+)                                      # Twitter ID
(/\w+)?                                     # Path
/img
/([^.]+)                                    # Image key
\.(jpg|png|gif)                             # Extension
(?::(orig|large|medium|small|thumb))?       # Size
""", re.X | re.IGNORECASE)

IMAGE4_PARTIAL_RG = re.compile(r"""
/(ext_tw_video_thumb|amplify_video_thumb)   # Type
/(\d+)                                      # Twitter ID
(/\w+)?                                     # Path
/img
/([^.]+)                                    # Image key
\?format=(jpg|png|gif)                      # Extension
(?:&name=(\w+))?$                           # Size
""", re.X | re.IGNORECASE)

VIDEO1_PARTIAL_RG = re.compile(r"""
/tweet_video
/([^.]+)                                  # Video key
\.(mp4)                                 # Extension
""", re.X | re.IGNORECASE)

VIDEO2_PARTIAL_RG = re.compile(r"""
/(ext_tw_video|amplify_video)           # Type
/(\d+)                                  # Twitter ID
(?:/\w+)?
/vid
(?:/avc1)?
/(\d+)x(\d+)                            # Dimensions
/([^.]+)                               # Video key
\.(mp4)                                 # Extension
""", re.X | re.IGNORECASE)

# ###### Full URL regexes

"""https://twitter.com/danboorubot/status/1617004230505537536"""

TWEET1_RG = re.compile(f'{TWITTER_HOST_RG.pattern}{TWEET1_PARTIAL_RG.pattern}', re.X | re.IGNORECASE)

"""https://twitter.com/i/web/status/1479489096045281283"""

TWEET2_RG = re.compile(f'{TWITTER_HOST_RG.pattern}{TWEET2_PARTIAL_RG.pattern}', re.X | re.IGNORECASE)

"""https://twitter.com/danboorubot"""

USERS1_RG = re.compile(f'{TWITTER_HOST_RG.pattern}{USERS1_PARTIAL_RG.pattern}', re.X | re.IGNORECASE)

"""https://twitter.com/intent/user?user_id=2807221321"""

USERS2_RG = re.compile(f'{TWITTER_HOST_RG.pattern}{USERS2_PARTIAL_RG.pattern}', re.X | re.IGNORECASE)

"""https://twitter.com/i/user/994169624659804161"""

USERS3_RG = re.compile(f'{TWITTER_HOST_RG.pattern}{USERS3_PARTIAL_RG.pattern}', re.X | re.IGNORECASE)

"""https://pbs.twimg.com/media/Es5NR-YVgAQzpJP.jpg:orig"""
"""http://pbs.twimg.com/tweet_video_thumb/EiWHH0HVgAAbEcF.jpg"""

IMAGE1_RG = re.compile(f'{TWIMG_HOST_RG.pattern}{IMAGE1_PARTIAL_RG.pattern}', re.X | re.IGNORECASE)

"""https://pbs.twimg.com/media/Es5NR-YVgAQzpJP?format=jpg&name=900x900"""

IMAGE2_RG = re.compile(f'{TWIMG_HOST_RG.pattern}{IMAGE2_PARTIAL_RG.pattern}', re.X | re.IGNORECASE)

"""http://pbs.twimg.com/ext_tw_video_thumb/1270031579470061568/pu/img/cLxRLtYjq_D10ome.jpg"""
"""https://pbs.twimg.com/amplify_video_thumb/1096312943845593088/img/VE7v_9MVr3tqZMNH.jpg"""

IMAGE3_RG = re.compile(f'{TWIMG_HOST_RG.pattern}{IMAGE3_PARTIAL_RG.pattern}', re.X | re.IGNORECASE)

"""https://pbs.twimg.com/ext_tw_video_thumb/1440389658647490560/pu/img/tZehLN5THk3Yyedt?format=jpg&name=orig"""

IMAGE4_RG = re.compile(f'{TWIMG_HOST_RG.pattern}{IMAGE4_PARTIAL_RG.pattern}', re.X | re.IGNORECASE)

"""https://video.twimg.com/tweet_video/EiWHH0HVgAAbEcF.mp4"""

VIDEO1_RG = re.compile(f'{TWVIDEO_HOST_RG.pattern}{VIDEO1_PARTIAL_RG.pattern}', re.X | re.IGNORECASE)

"""https://video.twimg.com/ext_tw_video/1270031579470061568/pu/vid/640x640/M54mOuT519Rb5eXs.mp4"""
"""https://video.twimg.com/amplify_video/1296680886113456134/vid/1136x640/7_ps073yayavGQUe.mp4"""

VIDEO2_RG = re.compile(f'{TWVIDEO_HOST_RG.pattern}{VIDEO2_PARTIAL_RG.pattern}', re.X | re.IGNORECASE)

SHORT_URL_REPLACE_RG = re.compile(r"""
https?://t\.co                         # Hostname
/ [\w-]+                               # Account
""", re.X | re.IGNORECASE)


# #### Network variables

REQUEST_METHODS = {
    'GET': requests.get,
    'POST': requests.post
}

XREQUEST_METHODS = {
    'GET': httpx.get,
    'POST': httpx.post
}

TWITTER_AUTH = "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xn" +\
               "Zz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"

TWITTER_USER_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',  # noqa: E501
    'authorization': 'Bearer ' + TWITTER_AUTH,
    'x-csrf-token': TWITTER_CSRF_TOKEN,
    'cookie': f'auth_token={TWITTER_USER_TOKEN}; ct0={TWITTER_CSRF_TOKEN}'
}

HAS_USER_AUTH = TWITTER_USER_TOKEN is not None and TWITTER_CSRF_TOKEN is not None
TWITTER_HEADERS = TWITTER_USER_HEADERS if HAS_USER_AUTH else None

TWITTER_ILLUST_TIMELINE_GRAPHQL_FEATURES = {
    "rweb_lists_timeline_redesign_enabled": True,
    "responsive_web_graphql_exclude_directive_enabled": True,
    "verified_phone_label_enabled": False,
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "tweetypie_unmention_optimization_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
    "view_counts_everywhere_api_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "responsive_web_twitter_article_tweet_consumption_enabled": False,
    "tweet_awards_web_tipping_enabled": False,
    "freedom_of_speech_not_reach_fetch_enabled": True,
    "standardized_nudges_misinfo": True,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": True,
    "responsive_web_media_download_video_enabled": False,
    "responsive_web_enhance_cards_enabled": False,
}

TWITTER_ILLUST_TIMELINE_GRAPHQL_FIELD_TOGGLES = {
    "withArticleRichContentState": False,
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

TWITTER_MEDIA_TIMELINE_GRAPHQL = {
    "includePromotedContent": False,
    "withSuperFollowsUserFields": True,
    "withDownvotePerspective": False,
    "withReactionsMetadata": False,
    "withReactionsPerspective": False,
    "withSuperFollowsTweetFields": True,
    "withClientEventToken": False,
    "withBirdwatchNotes": False,
    "withVoice": True,
    "withV2Timeline": True,
}

TWITTER_MEDIA_TIMELINE_FEATURES = {
    "responsive_web_graphql_timeline_navigation_enabled": False,
    "unified_cards_ad_metadata_container_dynamic_card_content_query_enabled": False,
    "dont_mention_me_view_api_enabled": True,
    "responsive_web_uc_gql_enabled": True,
    "vibe_api_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": False,
    "standardized_nudges_misinfo": True,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": False,
    "interactive_text_enabled": True,
    "responsive_web_text_conversations_enabled": False,
    "responsive_web_enhance_cards_enabled": True,
}

TWITTER_BASE_PARAMS = {
    "include_profile_interstitial_type": "1",
    "include_blocking": "1",
    "include_blocked_by": "1",
    "include_followed_by": "1",
    "include_want_retweets": "1",
    "include_mute_edge": "1",
    "include_can_dm": "1",
    "include_can_media_tag": "1",
    "include_ext_has_nft_avatar": "1",
    "include_ext_is_blue_verified": "1",
    "include_ext_verified_type": "1",
    "skip_status": "1",
    "cards_platform": "Web-12",
    "include_cards": "1",
    "include_ext_alt_text": "true",
    "include_ext_limited_action_results": "false",
    "include_ext_collab_control": "true",
    "include_ext_views": "true",
    "include_reply_count": "1",
    "include_quote_count": "true",
    "tweet_mode": "extended",
    "include_entities": "true",
    "include_user_entities": "true",
    "include_ext_media_color": "true",
    "include_ext_media_availability": "true",
    "include_ext_sensitive_media_warning": "true",
    "include_ext_edit_control": "true",
    "send_error_codes": "true",
    "simple_quoted_tweet": "true",
    "count": "20",
    "ext": "mediaStats,highlightedLabel,hasNftAvatar,voiceInfo,birdwatchPivot,enrichments,superFollowMetadata,unmentionInfo,editControl,collab_control,vibe",  # noqa: E501
}

TWITTER_SEARCH_PARAMS = {
    "tweet_search_mode": "live",
    "query_source": "typed_query",
    "pc": "1",
    "spelling_corrections": "1",
}

TWITTER_SEARCH_TIMELINE_VARIABLES = {
    "querySource": "typed_query",
    "product": "Latest",
}

TWITTER_SEARCH_TIMELINE_FEATURES = {
    "rweb_lists_timeline_redesign_enabled": True,
    "responsive_web_graphql_exclude_directive_enabled": True,
    "verified_phone_label_enabled": True,
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "tweetypie_unmention_optimization_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
    "view_counts_everywhere_api_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "responsive_web_twitter_article_tweet_consumption_enabled": False,
    "tweet_awards_web_tipping_enabled": False,
    "freedom_of_speech_not_reach_fetch_enabled": True,
    "standardized_nudges_misinfo": True,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": True,
    "responsive_web_media_download_video_enabled": False,
    "responsive_web_enhance_cards_enabled": False,
}

TWITTER_SEARCH_TIMELINE_FIELD_TOGGLES = {
    "withAuxiliaryUserLabels": False,
    "withArticleRichContentState": False,
}

# #### Subscription variables

PROCESS_FORM_CONFIG = {
    'type': {
        'field': RadioField,
        'kwargs': {
            'default': 'media',
            'choices': ['media', 'search', 'recover'],
        },
    },
    'last_id': {
        'name': "Last ID",
        'field': IntegerField,
        'kwargs': {
            'description': "Set as a stopping point for the media timeline.",
        },
    },
    'search_since': {
        'field': TextField,
    },
    'search_until': {
        'field': TextField,
    },
    'filter_links': {
        'field': BooleanField,
        'kwargs': {
            'default': False,
        },
    },
}

# #### Other variables

IMAGE_SERVER = 'https://pbs.twimg.com'
TWITTER_SIZES = [':orig', ':large', ':medium', ':small']

MINIMUM_QUERY_INTERVAL = 10

TOKEN_FILE = os.path.join(DATA_DIRECTORY, 'twittertoken.txt')
ERROR_TWEET_FILE = os.path.join(DATA_DIRECTORY, 'twittererror.json')

LAST_QUERY = None


# ## FUNCTIONS

# Illust

def image_illust_download_urls(illust):
    return list(filter(lambda x: image_url_mapper, illust.urls))


# Artist

def artist_links(artist):
    return {
        'main': artist_main_url(artist),
        'media': artist_media_url(artist),
        'likes': artist_likes_url(artist),
        'search': artist_search_url(artist),
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
    return bool(TWEET1_RG.match(url))


def partial_media_url(url):
    parse = urllib.parse.urlparse(url)
    match = IMAGE2_RG.match(url)
    query_addon = '?format=%s' % match.group(3) if match else ""
    return parse.path + query_addon


def is_media_url(url):
    return is_image_url(url) or is_video_url(url)


def is_partial_media_url(url):
    return is_partial_image_url(url) or is_partial_video_url(url)


def is_image_url(url):
    return bool(IMAGE1_RG.match(url) or IMAGE2_RG.match(url) or IMAGE3_RG.match(url) or IMAGE4_RG.match(url))


def is_partial_image_url(url):
    return bool(IMAGE1_PARTIAL_RG.match(url) or IMAGE2_PARTIAL_RG.match(url)
                or IMAGE3_PARTIAL_RG.match(url) or IMAGE4_PARTIAL_RG.match(url))


def is_video_url(url):
    return bool(VIDEO1_RG.match(url) or VIDEO2_RG.match(url))


def is_partial_video_url(url):
    return bool(VIDEO1_PARTIAL_RG.match(url) or VIDEO2_PARTIAL_RG.match(url))


def get_domain_from_partial_url(url):
    if is_partial_image_url(url):
        return 'pbs.twimg.com'
    if is_partial_video_url(url):
        return 'video.twimg.com'


def is_request_url(request_url):
    return is_post_url(request_url)


def get_illust_id(request_url):
    return int(TWEET1_RG.match(request_url).group(1))


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


def get_alternate_url(illust_url):
    media_url = get_media_url(illust_url)
    match = IMAGE1_RG.match(media_url)
    if match:
        path, key, ext, size = match.groups()
        return IMAGE_SERVER + rf"/{path}/{key}?format={ext}&name=orig"
    match = IMAGE2_RG.match(media_url)
    if match:
        path, key, ext, size = match.groups()
        return IMAGE_SERVER + rf"/{path}/{key}.{ext}:orig"


def get_preview_url(illust_url):
    return small_image_url(get_full_url(illust_url))


def original_image_url(image_url):
    return normalized_image_url(image_url) + ':orig'


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
    return 'https://' + illust_url.site.domain + illust_url.url


def get_sample_url(illust_url, original=False):
    addon = ':orig' if original else ""
    return 'https://' + illust_url.sample_site.domain + illust_url.sample_url + addon


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
    return artist.current_site_account if artist.current_site_account is not None else artist.site_accounts[0]


def artist_profile_urls(artist):
    profile_urls = ['https://twitter.com/intent/user?user_id=%d' % artist.site_artist_id]
    for site_account in artist.site_accounts:
        profile_urls += ['https://twitter.com/%s' % site_account]
    return profile_urls


def artist_booru_search_url(artist):
    return 'https://twitter.com/intent/user?user_id=%d' % artist.site_artist_id


def illust_commentaries_dtext(illust):
    if len(illust.commentaries) == 0:
        return []
    commentary = illust.commentaries[0]  # Twitter commentaries are unchangable.
    for tag in illust.tags:
        hashtag = '#' + tag
        hashtag_link = r'"%s":[https://twitter.com/hashtag/%s]' % (hashtag, tag)
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


def artist_search_url(artist):
    return f'https://twitter.com/search?src=typed_query&f=live&q=from%3A{artist.current_site_account}%20filter%3Alinks'


def process_twitter_timestring(time_string):
    try:
        return datetime.datetime.strptime(time_string, '%a %b %d %H:%M:%S +0000 %Y')
    except ValueError:
        pass


def convert_entity_text(twitter_data, key, url_subkeys, mention_subkeys=None):
    replace_entries = []
    text = twitter_data[key]
    text_start = 0
    retweet = False
    while text_start < len(text):
        char = text[text_start]
        if char == '@':
            retweet = True
        elif retweet:
            retweet = char != ' '
        else:
            break
        text_start += 1
    url_entries = safe_get(twitter_data, 'entities', *url_subkeys) or []
    for url_entry in url_entries:
        replace_entries.append({
            'replace': url_entry['expanded_url'],
            'start_index': url_entry['indices'][0],
            'end_index': url_entry['indices'][1],
        })
    if mention_subkeys is not None:
        mention_entries = safe_get(twitter_data, 'entities', *mention_subkeys) or []
        for mention in mention_entries:
            if mention['indices'][0] < text_start:
                continue
            user_id = mention['id_str']
            screen_name = mention['screen_name']
            replace_entries.append({
                'replace': f'@{screen_name} (twuser #{user_id})',
                'start_index': mention['indices'][0],
                'end_index': mention['indices'][1],
            })
    replace_entries.sort(key=lambda x: x['start_index'], reverse=True)
    for entry in replace_entries:
        text = text[:entry['start_index']] + entry['replace'] + text[entry['end_index']:]
    text = text[text_start:]
    if 'in_reply_to_status_id_str' in twitter_data:
        pretext = "Replying to "
        if 'in_reply_to_screen_name' in twitter_data and 'in_reply_to_user_id_str' in twitter_data:
            screen_name = twitter_data['in_reply_to_screen_name']
            user_id_str = twitter_data['in_reply_to_user_id_str']
            pretext = "@%s (twuser #%s)\r\n" % (screen_name, user_id_str)
        pretext += "=> twitter #%s" % twitter_data['in_reply_to_status_id_str']
        text = pretext + '\r\n\r\n' + text
    return html.unescape(text)


#   Database

def source_prework(site_illust_id):
    illust = get_site_illust(site_illust_id, SITE.id)
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
    save_api_data(tweets, 'id_str', SITE.id, api_data_type.illust.id)
    twusers = []
    user_ids = set()
    for i in range(len(twitter_data)):
        id_str = safe_get(twitter_data[i], 'result', 'core', 'user_results', 'result', 'rest_id')
        user = safe_get(twitter_data[i], 'result', 'core', 'user_results', 'result', 'legacy')
        if user is None or id_str in user_ids:
            continue
        user['id_str'] = id_str
        twusers.append(user)
        user_ids.add(id_str)
    save_api_data(twusers, 'id_str', SITE.id, api_data_type.artist.id)


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


# #### Network auxiliary functions

def get_global_objects(data, type_name):
    objects = safe_get(data['body'], 'globalObjects', type_name)
    if type(objects) is not dict:
        if DEBUG_MODE:
            log_network_error('sources.twitter.get_global_objects', data['response'])
        raise Exception("Global data not found.")
    return list(objects.values())


def get_twitter_timeline_cursor(type_name, instruction, entryname):
    if type_name == "addEntries":
        for entry in instruction[type_name]['entries']:
            if entry['entryId'].find(entryname) > -1:
                cursor_entry = entry
                break
        else:
            cursor_entry = None
        if cursor_entry is not None:
            return safe_get(cursor_entry, 'content', 'operation', 'cursor', 'value')
    elif type_name == "replaceEntry" and instruction[type_name]['entryIdToReplace'].find(entryname) > -1:
        return safe_get(instruction[type_name], 'entry', 'content', 'operation', 'cursor', 'value')


def get_twitter_scroll_bottom_cursor(data):
    instructions = safe_get(data['body'], 'timeline', 'instructions')
    if type(instructions) is not list:
        if DEBUG_MODE:
            log_network_error('sources.twitter.get_twitter_scroll_bottom_cursor', data['response'])
        raise Exception("Invalid JSON response.")
    for instruction in instructions:
        for type_name in instruction:
            cursor = get_twitter_timeline_cursor(type_name, instruction, 'cursor-bottom')
            if cursor is not None:
                return cursor


def timeline_iterator(data, cursor, tweet_ids, seen_users, user_id=None, last_id=None, v2=False, **kwargs):
    if v2:
        results = get_graphql_timeline_entries_v2(data['body'])
    else:
        results =\
            {
                'tweets': {tweet['id_str']: tweet for tweet in get_global_objects(data, 'tweets')},
                'users': {user['id_str']: user for user in get_global_objects(data, 'users')},
            }
    tweets = [tweet for tweet in results['tweets'].values()]
    if len(results['tweets']) == 0:
        # Only check on the first iteration
        if cursor[0] is None and len(results['users']) == 0:
            return
        print("Reached end of timeline!")
        return True
    media_tweets = [tweet for tweet in tweets if safe_get(tweet, 'entities', 'media')]
    save_api_data(media_tweets, 'id_str', SITE.id, api_data_type.illust.id)
    user_tweets = [tweet for tweet in media_tweets if user_id is None or tweet['user_id_str'] == str(user_id)]
    tweet_ids.extend(int(tweet['id_str']) for tweet in user_tweets)
    twusers = [twuser for twuser in results['users'].values() if twuser['id_str'] not in seen_users]
    save_api_data(twusers, 'id_str', SITE.id, api_data_type.artist.id)
    seen_users.extend(twuser['id_str'] for twuser in twusers)
    if last_id is not None and any(x for x in tweet_ids if x <= last_id):
        valid_ids = [x for x in tweet_ids if x > last_id]
        tweet_ids.clear()
        tweet_ids.extend(valid_ids)
        return True
    found_cursor = results['cursors']['bottom'] if v2 else get_twitter_scroll_bottom_cursor(data)
    if found_cursor is None:
        print("Reached end of timeline!")
        return True
    cursor[0] = found_cursor
    return False


def get_timeline(page_func, job_id=None, job_status={}, **kwargs):
    page = 1
    cursor = [None]
    tweet_ids = []
    seen_users = []
    lowest_tweet_id = None
    count = 0
    while True:
        data = page_func(cursor=cursor[0], **kwargs)
        if data['error']:
            return data['message']
        if lowest_tweet_id is not None:
            timestamp = snowflake_to_epoch(lowest_tweet_id)
            timeval = datetime_from_epoch(timestamp)
            bookmark = f"twitter #{lowest_tweet_id} @ {timeval}"
        else:
            bookmark = "initial"
        print(f"Gettime timeline page #{page} - {bookmark}")
        if job_id is not None and len(tweet_ids) > count:
            job_status['temp_ids'] = tweet_ids
            print_info("Saving temp ids:", job_status['temp_ids'])
            update_job_status(job_id, job_status)
            count = len(tweet_ids)
        old_tweet_ids = tweet_ids.copy()
        result = timeline_iterator(data, cursor, tweet_ids, seen_users, **kwargs)
        tweet_ids = list(set(tweet_ids))
        if result is None:
            print(f"No media tweets found on page #{page}")
            return
        elif result:
            return sorted(tweet_ids, key=int, reverse=True)
        if len(tweet_ids) > len(old_tweet_ids):
            lowest_tweet_id = min(id for id in tweet_ids if id not in old_tweet_ids)
        page += 1


# #### Network functions

def check_guest_auth(func):
    def wrapper(*args, **kwargs):
        if not HAS_USER_AUTH and (TWITTER_HEADERS is None or not check_token_file()):
            authenticate_guest()
        return func(*args, **kwargs)
    return wrapper


def authenticate_guest(override=False):
    global TWITTER_HEADERS
    if HAS_USER_AUTH:
        raise Exception("Should not authenticate with user auth.")
    TWITTER_HEADERS = {
        'authorization': 'Bearer %s' % TWITTER_AUTH
    }
    guest_token = load_guest_token() if not override else None
    if guest_token is None:
        print("Authenticating as guest...")
        data = twitter_request('https://api.twitter.com/1.1/guest/activate.json', 'POST', False)
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


def check_request_wait(wait):
    if not wait:
        return
    next_wait = get_next_wait('twitter')
    if next_wait is not None:
        sleep_time = next_wait - get_current_time().timestamp()
        if sleep_time > 0.0:
            update_next_wait('twitter', MINIMUM_QUERY_INTERVAL + sleep_time)
            print_info("Twitter request: sleeping -", sleep_time)
            time.sleep(sleep_time)
            return
    update_next_wait('twitter', MINIMUM_QUERY_INTERVAL)


@check_guest_auth
def twitter_request(url, method='GET', wait=True, use_httpx=False):
    check_request_wait(wait)
    reauthenticated = False
    rq_methods = REQUEST_METHODS if not use_httpx else XREQUEST_METHODS
    for i in range(3):
        try:
            response = rq_methods[method](url, headers=TWITTER_HEADERS, timeout=10)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError, httpx.ConnectTimeout) as e:
            print_warning("Pausing for network timeout...")
            error = e
            time.sleep(5)
            continue
        if response.status_code == 200:
            break
        if not reauthenticated and reauthentication_check(response):
            authenticate_guest(True)
            reauthenticated = True
        elif response.status_code == 429:
            print_warning("Pausing for requests exceeded...")
            error = "HTTP 429: Too many requests - rate limit exceeded."
            time.sleep(300)
        elif response.status_code in [503]:
            print_warning("Pausing for server error:", response.text)
            error = "HTTP 503: Server error."
            time.sleep(60)
        else:
            reason = getattr(response, 'reason', None)
            print_error("\n%s\nHTTP %d: %s (%s)" % (url, response.status_code, reason, response.text))
            if DEBUG_MODE:
                log_network_error('sources.twitter.twitter_request', response)
            msg = "HTTP %d - %s" % (response.status_code, reason)
            return {'error': True, 'message': msg, 'response': response}
    else:
        print_error("Connection errors exceeded!")
        message = error if isinstance(error, str) else repr(error)
        return {'error': True, 'message': message}
    try:
        data = response.json()
    except Exception:
        return {'error': True, 'message': "Error decoding response into JSON.", 'response': response}
    return {'error': False, 'body': data, 'response': response}


def get_graphql_timeline_entries(data, found_tweets):
    for key in data:
        if key == 'tweet_results':
            found_tweets.append(data[key])
        elif type(data[key]) is list:
            for i in range(len(data[key])):
                if type(data[key][i]) is dict:
                    found_tweets = get_graphql_timeline_entries(data[key][i], found_tweets)
        elif type(data[key]) is dict:
            found_tweets = get_graphql_timeline_entries(data[key], found_tweets)
    return found_tweets


def get_graphql_timeline_entries_v2(data, retdata=None):
    retdata = retdata or {'tweets': {}, 'retweets': {}, 'users': {}, 'cursors': {}, 'retweeted_ids': []}
    for key in data:
        if key == '__typename':
            if data[key] == 'TweetWithVisibilityResults' and 'tweet' in data and 'legacy' in data['tweet']:
                node_data = data['tweet']
                key = 'tweets' if 'retweeted_status_result' not in node_data['legacy'] else 'retweets'
            elif data[key] == 'Tweet' and 'legacy' in data:
                node_data = data
                key = 'tweets' if 'retweeted_status_result' not in node_data['legacy'] else 'retweets'
            elif data[key] == 'User' and 'legacy' in data:
                node_data = data
                key = 'users'
            elif data[key] == "TimelineTimelineCursor":
                cursor_key = data['cursorType'].lower()
                retdata['cursors'][cursor_key] = data['value']
                continue
            else:
                continue
            if 'rest_id' not in node_data:
                continue
            if key == 'retweets':
                retweet = get_graphql_timeline_entries_v2(node_data['legacy']['retweeted_status_result'])
                retweet_id = node_data['legacy']['retweet_id'] = next(key for key in retweet['tweets'])
                retdata['retweeted_ids'].append(retweet_id)
            item = node_data['legacy']
            id_str = item['id_str'] = node_data['rest_id']
            if id_str in retdata['retweeted_ids']:
                continue
            retdata[key][id_str] = node_data['legacy']
        elif type(data[key]) is list:
            for i in range(len(data[key])):
                if type(data[key][i]) is dict and not ('type' in data[key][i] and data[key][i]['type'] == 'TimelinePinEntry'):
                    retdata = get_graphql_timeline_entries_v2(data[key][i], retdata)
        elif type(data[key]) is dict and not ('type' in data[key] and data[key]['type'] == 'TimelinePinEntry'):
            retdata = get_graphql_timeline_entries_v2(data[key], retdata)
    return retdata


def get_twitter_illust_timeline(illust_id):
    print("Getting twitter #%d" % illust_id)
    illust_id_str = str(illust_id)
    variables = TWITTER_ILLUST_TIMELINE_GRAPHQL.copy()
    variables['focalTweetId'] = illust_id_str
    features = TWITTER_ILLUST_TIMELINE_GRAPHQL_FEATURES.copy()
    field_toggles = TWITTER_ILLUST_TIMELINE_GRAPHQL_FIELD_TOGGLES.copy()
    urladdons = urllib.parse.urlencode({'variables': json.dumps(variables),
                                        'features': json.dumps(features),
                                        'fieldToggles': json.dumps(field_toggles)})
    data = twitter_request("https://twitter.com/i/api/graphql/q94uRCEn65LZThakYcPT6g/TweetDetail?%s" % urladdons,
                           use_httpx=True)
    try:
        if data['error']:
            return create_error('sources.twitter.get_twitter_illust_timeline', data['message'])
        found_tweets = get_graphql_timeline_entries(data['body'], [])
    except Exception as e:
        msg = "Error parsing Twitter data: %s" % str(e)
        return create_error('sources.twitter.get_twitter_illust_timeline', msg)
    if len(found_tweets) == 0:
        put_get_json(ERROR_TWEET_FILE, 'wb', data['body'], unicode=True)
        return create_error('sources.twitter.get_twitter_illust_timeline', "No tweets found in data.")
    # Normalize the hierarchical position of tweet info
    for tweet in found_tweets:
        if 'tweet' in safe_get(tweet, 'result'):
            for k in tweet['result']['tweet']:
                tweet['result'][k] = tweet['result']['tweet'][k]
    tweet_ids = [safe_get(tweet_entry, 'result', 'rest_id') for tweet_entry in found_tweets]
    if illust_id_str not in tweet_ids:
        put_get_json(ERROR_TWEET_FILE, 'wb', data['body'], unicode=True)
        return create_error('sources.twitter.get_twitter_illust_timeline', "Tweet not found: %d" % illust_id)
    return found_tweets


def get_media_page(user_id, cursor=None):
    params = TWITTER_BASE_PARAMS.copy()
    if cursor is not None:
        params['cursor'] = cursor
    url_params = urllib.parse.urlencode(params)
    return twitter_request(("https://api.twitter.com/2/timeline/media/%s.json?" % user_id) + url_params)


def get_media_page_v2(user_id, count, cursor=None):
    variables = TWITTER_MEDIA_TIMELINE_GRAPHQL.copy()
    features = TWITTER_MEDIA_TIMELINE_FEATURES.copy()
    variables['userId'] = str(user_id)
    variables['count'] = count
    if cursor is not None:
        variables['cursor'] = cursor
    url_params = urllib.parse.urlencode({'variables': json.dumps(variables), 'features': json.dumps(features)})
    return twitter_request("https://twitter.com/i/api/graphql/_vFDgkWOKL_U64Y2VmnvJw/UserMedia?" + url_params,
                           use_httpx=True)


def get_search_page(query, cursor=None):
    params = TWITTER_BASE_PARAMS.copy()
    params.update(TWITTER_SEARCH_PARAMS)
    params['q'] = query
    if cursor is not None:
        params['cursor'] = cursor
    url_params = urllib.parse.urlencode(params)
    return twitter_request("https://api.twitter.com/2/search/adaptive.json?" + url_params, use_httpx=True)


def get_search_page_v2(query, count, cursor=None):
    variables = TWITTER_SEARCH_TIMELINE_VARIABLES.copy()
    features = TWITTER_SEARCH_TIMELINE_FEATURES.copy()
    field_toggles = TWITTER_SEARCH_TIMELINE_FIELD_TOGGLES.copy()
    variables['rawQuery'] = query
    variables['count'] = count
    if cursor is not None:
        variables['cursor'] = cursor
    url_params = urllib.parse.urlencode({'variables': json.dumps(variables),
                                         'features': json.dumps(features),
                                         'fieldToggles': json.dumps(field_toggles)})
    return twitter_request("https://twitter.com/i/api/graphql/KUnA_SzQ4DMxcwWuYZh9qg/SearchTimeline?" + url_params)


def populate_twitter_media_timeline(user_id, last_id, job_id=None, job_status={}, **kwargs):
    print("Populating from media page: %d" % (user_id))

    def page_func(cursor, **kwargs):
        nonlocal user_id, job_id, job_status, page
        job_status['range'] = 'media:' + str(page)
        update_job_status(job_id, job_status)
        page += 1
        if HAS_USER_AUTH:
            return get_media_page_v2(user_id, count, cursor)
        else:
            return get_media_page(user_id, cursor)

    count = 100 if last_id is None else 20
    page = 1
    tweet_ids = get_timeline(page_func, user_id=user_id, last_id=last_id, job_id=job_id, job_status=job_status,
                             v2=HAS_USER_AUTH)
    return create_error('sources.twitter.populate_twitter_media_timeline', tweet_ids)\
        if isinstance(tweet_ids, str) else tweet_ids


def populate_twitter_search_timeline(account, since_date, until_date, filter_links,
                                     job_id=None, job_status={}, **kwargs):
    query = f"from:{account}"
    if since_date is not None:
        query += f" since:{since_date}"
    else:
        since_date = ""
    if until_date is not None:
        query += f" until:{until_date}"
    else:
        until_date = ""
    if filter_links:
        query += " filter:links"
    print("Populating from search page: %s" % query)

    def page_func(cursor, **kwargs):
        nonlocal query, job_id, job_status, page
        job_status['range'] = since_date + '..' + until_date + ':' + str(page)
        update_job_status(job_id, job_status)
        page += 1
        if HAS_USER_AUTH:
            return get_search_page_v2(query, count, cursor)
        else:
            return get_search_page(query, cursor)

    count = 100
    page = 1
    tweet_ids = get_timeline(page_func, job_id=job_id, job_status=job_status, v2=HAS_USER_AUTH, **kwargs)
    return create_error('sources.twitter.populate_twitter_search_timeline', tweet_ids)\
        if isinstance(tweet_ids, str) else tweet_ids


def get_twitter_illust(illust_id):
    print("Getting twitter #%d" % illust_id)
    request_url = 'https://api.twitter.com/1.1/statuses/lookup.json?id=%d' % illust_id +\
                  '&trim_user=true&tweet_mode=extended&include_quote_count=true&include_reply_count=true'
    data = twitter_request(request_url, use_httpx=True)
    if data['error']:
        return create_error('sources.twitter.get_twitter_illust', data['message'])
    if len(data['body']) == 0:
        return create_error('sources.twitter.get_twitter_illust', "Tweet not found: %d" % illust_id)
    return data['body'][0]


def get_twitter_illust_v2(illust_id):
    print("Getting twitter #%d" % illust_id)
    illust_id_str = str(illust_id)
    twitter_data = get_twitter_illust_timeline(illust_id)
    if is_error(twitter_data):
        return twitter_data
    for i in range(len(twitter_data)):
        tweet = safe_get(twitter_data[i], 'result', 'legacy')
        if tweet is not None and tweet['id_str'] == illust_id_str:
            return tweet
    return create_error('sources.twitter.get_twitter_illust_v2', "Tweet not found: %d" % illust_id)


def get_twitter_user_id(account):
    print("Getting user ID: %s" % account)
    jsondata = {
        'screen_name': account,
        'withHighlightedLabel': False
    }
    urladdons = urllib.parse.urlencode({'variables': json.dumps(jsondata)})
    request_url = 'https://twitter.com/i/api/graphql/Vf8si2dfZ1zmah8ePYPjDQ/' +\
                  'UserByScreenNameWithoutResults?%s' % urladdons
    data = twitter_request(request_url, wait=False, use_httpx=True)
    if data['error']:
        return create_error('sources.twitter.get_user_id', data['message'])
    return safe_get(data, 'body', 'data', 'user', 'rest_id')


def get_twitter_artist(artist_id):
    print("Getting user #%d" % artist_id)
    jsondata = {
        'userId': str(artist_id),
        'withHighlightedLabel': False,
    }
    urladdons = urllib.parse.urlencode({'variables': json.dumps(jsondata)})
    request_url = 'https://twitter.com/i/api/graphql/WN6Hck-Pwm-YP0uxVj1oMQ/' +\
                  'UserByRestIdWithoutResults?%s' % urladdons
    data = twitter_request(request_url, use_httpx=True)
    if data['error']:
        return create_error('sources.twitter.get_twitter_artist', data['message'])
    twitterdata = data['body']
    if 'errors' in twitterdata and len(twitterdata['errors']):
        msg = 'Twitter error: ' + '; '.join([error['message'] for error in twitterdata['errors']])
        return create_error('sources.twitter.get_twitter_artist', msg)
    userdata = safe_get(twitterdata, 'data', 'user')
    if userdata is None or 'rest_id' not in userdata or 'legacy' not in userdata:
        msg = "Error parsing data: %s" % json.dumps(twitterdata)
        return create_error('sources.twitter.get_twitter_artist', msg)
    retdata = userdata['legacy']
    retdata['id_str'] = userdata['rest_id']
    return retdata


# #### Param functions

# ###### ILLUST

def get_tweet_commentary(twitter_data):
    text = convert_entity_text(twitter_data, 'full_text', ['urls'], ['user_mentions'])
    text = fixup_crlf(SHORT_URL_REPLACE_RG.sub('', text).strip())
    if safe_get(twitter_data, 'is_quote_status'):
        # If the quoted tweet is no longer available, then it will still register as a quote tweet.
        quote_tweet = safe_get(twitter_data, 'quoted_status_permalink', 'expanded')
        if quote_tweet and not text.endswith(quote_tweet):
            text += ' ' + quote_tweet
    media = safe_get(twitter_data, 'extended_entities', 'media')
    if media is not None and len(media):
        alt_text_items = [(i + 1, item['ext_alt_text'])
                          for (i, item) in enumerate(media)
                          if safe_check(item, str, 'ext_alt_text')]
        if len(alt_text_items):
            text += '\r\n\r\n' + '\r\n'.join(["{IMAGE #%d}\r\n%s" % (i, alt_text) for (i, alt_text) in alt_text_items])
        media_text_items = set()
        for item in media:
            media_tags = safe_get(item, 'features', 'all', 'tags')
            if media_tags is not None and len(media_tags):
                media_text_items.update([f"@{tag['screen_name']} (twuser #{tag['user_id']})" for tag in media_tags])
        if len(media_text_items):
            text += '\r\n\r\nMentions:\r\n' + '\r\n'.join(media_text_items)
    return text.strip()


def get_illust_tags(tweet):
    tag_data = safe_get(tweet, 'entities', 'hashtags') or []
    return list(set(entry['text'].lower() for entry in tag_data))


def get_illust_url_info(entry, media_type):
    query_addon = ""
    if entry['type'] == 'photo' or (media_type == 'image' and entry['type'] in ['animated_gif', 'video']):
        parse = urllib.parse.urlparse(entry['media_url_https'])
        dimensions = (entry['original_info']['width'], entry['original_info']['height'])
        match = IMAGE2_RG.match(entry['media_url_https'])
        if match:
            query_addon = '?format=%s' % match.group(3)
    elif entry['type'] == 'video' or (media_type == 'video' and entry['type'] == 'animated_gif'):
        variants = entry['video_info']['variants']
        valid_variants = [variant for variant in variants if 'bitrate' in variant]
        max_bitrate = max(map(lambda x: x['bitrate'], valid_variants))
        max_video = next(filter(lambda x: x['bitrate'] == max_bitrate, valid_variants))
        parse = urllib.parse.urlparse(max_video['url'])
        dimensions = (entry['sizes']['large']['w'], entry['sizes']['large']['h'])
    else:
        return None, None, None
    site = site_descriptor.get_site_from_domain(parse.netloc)
    url = parse.path + query_addon
    return url, site, dimensions


def get_tweet_illust_urls(tweet):
    media_urls = get_tweet_image_urls(tweet)
    video_urls = get_tweet_video_urls(tweet)
    for i, video_url in enumerate(video_urls):
        media_url = next((media for media in media_urls if media['order'] == video_url['order']), None)
        if media_url is None:
            continue
        video_url.update(
            sample_site_id=media_url['site_id'],
            sample_url=media_url['url']
        )
        index = media_urls.index(media_url)
        media_urls[index] = video_url
    return media_urls


def get_tweet_image_urls(tweet):
    illust_urls = []
    url_data = safe_get(tweet, 'entities', 'media') or []
    for i in range(len(url_data)):
        url, site, dimensions = get_illust_url_info(url_data[i], 'image')
        if url is None:
            continue
        illust_urls.append({
            'site_id': site.id,
            'url': url,
            'width': dimensions[0],
            'height': dimensions[1],
            'order': i + 1,
            'active': True,
        })
    return illust_urls


def get_tweet_video_urls(tweet):
    video_urls = []
    url_data = safe_get(tweet, 'extended_entities', 'media') or []
    for i in range(len(url_data)):
        if url_data[i]['type'] not in ['animated_gif', 'video']:
            continue
        url, site, dimensions = get_illust_url_info(url_data[i], 'video')
        if url is None:
            continue
        video_urls.append({
            'site_id': site.id,
            'url': url,
            'width': dimensions[0],
            'height': dimensions[1],
            'order': i + 1,
            'active': True,
        })
    return video_urls


def get_illust_parameters_from_tweet(tweet):
    site_artist_id = safe_get(tweet, 'user', 'id_str') or safe_get(tweet, 'user_id_str')
    return {
        'site_id': SITE.id,
        'site_illust_id': int(tweet['id_str']),
        'site_created': process_twitter_timestring(tweet['created_at']),
        'pages': len(tweet['extended_entities']['media']),
        'score': tweet['favorite_count'],
        'retweets': tweet['retweet_count'],
        'replies': tweet.get('reply_count'),
        'quotes': tweet.get('quote_count'),
        'tags': get_illust_tags(tweet),
        'commentaries': get_tweet_commentary(tweet) or None,
        'illust_urls': get_tweet_illust_urls(tweet),
        'active': True,
        'site_artist_id': int(site_artist_id) if site_artist_id is not None else None,
    }


# ###### ARTIST

def get_twuser_profile(twitter_data):
    return fixup_crlf(convert_entity_text(twitter_data, 'description', ['description', 'urls']))


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
        'site_id': SITE.id,
        'site_artist_id': int(twuser['id_str']),
        'site_created': process_twitter_timestring(twuser['created_at']),
        'current_site_account': twuser['screen_name'],
        'active': True,
        'primary': True,
        'names': [twuser['name']],
        'site_accounts': [twuser['screen_name']],
        'profiles': get_twuser_profile(twuser) or None,
        'webpages': get_twuser_webpages(twuser),
    }


# #### Data lookup functions

def get_artist_api_data(site_artist_id, reterror=False):
    twuser = get_api_artist(site_artist_id, SITE.id)
    if twuser is None:
        twuser = get_twitter_artist(site_artist_id)
        if is_error(twuser):
            return twuser if reterror else None
        save_api_data([twuser], 'id_str', SITE.id, api_data_type.artist.id)
    return twuser


def get_artist_data(site_artist_id):
    twuser = get_artist_api_data(site_artist_id)
    if twuser is None:
        return {'active': False}
    return get_artist_parameters_from_twuser(twuser)


def get_illust_api_data(site_illust_id):
    tweet = get_api_illust(site_illust_id, SITE.id)
    if tweet is None:
        tweet = get_twitter_illust_v2(site_illust_id)
        if is_error(tweet):
            return
        save_api_data([tweet], 'id_str', SITE.id, api_data_type.illust.id)
    return tweet


def get_illust_data(site_illust_id):
    tweet = get_illust_api_data(site_illust_id)
    if tweet is None:
        return {'active': False}
    return get_illust_parameters_from_tweet(tweet)


def get_artist_id_by_illust_id(site_illust_id):
    tweet = get_illust_api_data(site_illust_id)
    site_artist_id = safe_get(tweet, 'user', 'id_str') or safe_get(tweet, 'user_id_str')
    return int(site_artist_id) if site_artist_id is not None else None


# #### Other

def print_auth():
    print("AUTH_TOKEN:", TWITTER_USER_TOKEN)
    print("CT0:", TWITTER_CSRF_TOKEN)


def snowflake_to_epoch(snowflake):
    return ((snowflake >> 22) + 1288834974657) / 1000.0


def snowflake_to_timestring(snowflake):
    timestamp = snowflake_to_epoch(snowflake)
    timeval = datetime_from_epoch(timestamp)
    return timeval.isoformat()


def populate_artist_recheck_active(artist):
    twuser = get_artist_api_data(artist.site_artist_id, reterror=True)
    if is_error(twuser):
        inactivate_artist(artist)
        return twuser
    # The timeline was empty of any tweets
    return []


def populate_artist_illusts_from_media_timeline(artist, job_id, last_id):
    job_status = get_job_status_data(job_id) or {}
    if job_status.get('timeline') != 'media':
        job_status.pop('ids', None)
        job_status.pop('temp_ids', None)
        job_status['timeline'] = 'media'
    job_status['stage'] = 'querying'
    tweet_ids = populate_twitter_media_timeline(artist.site_artist_id, last_id, job_id=job_id, job_status=job_status)
    return populate_artist_recheck_active(artist) if tweet_ids is None else tweet_ids


def populate_artist_illusts_from_search_timeline(artist, job_id, since_date, until_date, filter_links):
    # Get the lastest screenname for the search timeline
    params = get_artist_data(artist.site_artist_id)
    update_artist(artist, params)
    job_status = get_job_status_data(job_id) or {}
    if job_status.get('timeline') != 'search':
        job_status.pop('ids', None)
        job_status.pop('temp_ids', None)
        job_status['timeline'] = 'search'
    job_status['stage'] = 'querying'
    since_date = since_date if since_date is not None and re.match(r'\d{4}-\d{2}-\d{2}', since_date) else None
    until_date = until_date if until_date is not None and re.match(r'\d{4}-\d{2}-\d{2}', until_date) else None
    tweet_ids = populate_twitter_search_timeline(artist.current_site_account, since_date, until_date, filter_links,
                                                 user_id=artist.site_artist_id, job_id=job_id, job_status=job_status)
    return populate_artist_recheck_active(artist) if tweet_ids is None else tweet_ids


def populate_all_artist_illusts(artist, job_id=None, params=None):
    if params is None:
        params = {
            'type': 'media',
            'last_id': artist.last_illust_id,
        }
    elif params['type'] == 'search':
        params['last_id'] = None
    if params['type'] == 'search' and params['search_since'] is None and params['search_until'] is None and params['last_id'] is None:
        raise Exception("Invalid process parameters for search timeline.")
    if params['type'] == 'media':
        return populate_artist_illusts_from_media_timeline(artist, job_id, params['last_id'])
    if params['type'] == 'search':
        return populate_artist_illusts_from_search_timeline(artist, job_id, params['search_since'],
                                                            params['search_until'], params['filter_links'])
    if params['type'] == 'recover':
        job_status = get_job_status_data(job_id) or {}
        return job_status.pop('temp_ids', [])
    return []
