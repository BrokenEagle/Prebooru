# APP/SOURCES/TWITTER.PY

# ##PYTHON IMPORTS
import time
import requests

# ##LOCAL IMPORTS
from ..config import DANBOORU_HOSTNAME
from ..logical.utility import AddDictEntry


# ##FUNCTIONS

def DanbooruRequest(url, params=None, long=False):
    send_method = requests.post if long else requests.get
    send_data = params if long else None
    params = None if long else params
    if long:
        send_data = send_data or {}
        send_data['_method'] = 'get'
    for i in range(3):
        try:
            response = send_method(DANBOORU_HOSTNAME + url, params=params, data=send_data, timeout=10)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            print("Pausing for network timeout...")
            time.sleep(5)
            continue
        break
    else:
        return {'error': True, 'message': "Connection errors exceeded."}
    if response.status_code == 200:
        return {'error': False, 'json': response.json()}
    else:
        return {'error': True, 'message': "HTTP %d: %s" % (response.status_code, response.reason)}


def GetArtistByID(id, include_urls=False):
    params = {'only': 'name,urls'} if include_urls else None
    request_url = '/artists/%d.json' % id
    data = DanbooruRequest(request_url, params)
    if data['error']:
        return data
    return {'error': False, 'artist': data['json']}


def GetArtistsByUrl(url):
    request_url = '/artist_urls.json'
    params = {
        'search[normalized_url]': url,
        'only': 'url,artist',
        'limit': 1000,
    }
    data = DanbooruRequest(request_url, params)
    if data['error']:
        return data
    artists = [artist_url['artist'] for artist_url in data['json']]
    return {'error': False, 'artists': artists}


def GetArtistsByMultipleUrls(url_list):
    request_url = '/artist_urls.json'
    params = {
        'search[normalized_url_space]': ' '.join(url_list),
        'only': 'normalized_url,artist',
        'limit': 1000,
    }
    data = DanbooruRequest(request_url, params)
    if data['error']:
        return data
    retdata = {}
    for artist_url in data['json']:
        AddDictEntry(retdata, artist_url['normalized_url'], artist_url['artist'])
    return {'error': False, 'data': retdata}


def GetPostsByMD5s(md5_list):
    request_url = '/posts.json'
    params = {
        'tags': 'md5:' + ','.join(md5_list),
        'limit': 100,
    }
    data = DanbooruRequest(request_url, params)
    if data['error']:
        return data
    return {'error': False, 'posts': [post for post in data['json'] if 'md5' in post]}
