# APP/SOURCES/TWITTER.PY

# ##PYTHON IMPORTS
import time
import requests

# ##LOCAL IMPORTS
from ..config import DANBOORU_HOSTNAME
from ..logical.utility import AddDictEntry


# ##FUNCTIONS

def DanbooruRequest(url, params=None):
    for i in range(3):
        try:
            response = requests.get(DANBOORU_HOSTNAME + url, params=params, timeout=10)
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
