# APP/LOGICAL/SOURCES/DANBOORU_SRC.PY

# ## PYTHON IMPORTS
import time

# ## EXTERNAL IMPORTS
import requests

# ## PACKAGE IMPORTS
from config import DANBOORU_USERNAME, DANBOORU_APIKEY, DANBOORU_HOSTNAME
from utility.data import add_dict_entry


# ## GLOBAL VARIABLES

DATA_FUNCTIONS = ['post']
REQUEST_METHODS = {
    'get': requests.get,
    'post': requests.post,
}
REQUEST_AUTH = (DANBOORU_USERNAME, DANBOORU_APIKEY)\
    if DANBOORU_USERNAME is not None and DANBOORU_APIKEY is not None\
    else None


# ## FUNCTIONS

def danbooru_request(url, params=None, files=None, long=False, method='get'):
    method = 'post' if long else method
    data = params if method in DATA_FUNCTIONS else None
    params = params if method not in DATA_FUNCTIONS else None
    if long:
        data = data or {}
        data['_method'] = 'get'
    for i in range(3):
        try:
            response = REQUEST_METHODS[method](DANBOORU_HOSTNAME + url, params=params, data=data, files=files,
                                               timeout=10, auth=REQUEST_AUTH)
        except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError):
            print("Pausing for network timeout...")
            time.sleep(5)
            continue
        break
    else:
        return {'error': True, 'message': "Connection errors exceeded."}
    if response.status_code in [200, 201]:
        return {'error': False, 'json': response.json()}
    else:
        return {'error': True, 'message': "HTTP %d: %s" % (response.status_code, response.reason)}


def get_artist_by_id(id, include_urls=False):
    params = {'only': 'name,urls,is_banned,is_deleted'} if include_urls else None
    request_url = '/artists/%d.json' % id
    data = danbooru_request(request_url, params)
    if data['error']:
        return data
    return {'error': False, 'artist': data['json']}


def get_artists_by_ids(id_list):
    params = {
        'search[id]': ','.join(map(str, id_list)),
        'limit': len(id_list),
    }
    request_url = '/artists.json'
    data = danbooru_request(request_url, params)
    if data['error']:
        return data
    return {'error': False, 'artists': data['json']}


def get_artists_by_url(url):
    request_url = '/artist_urls.json'
    params = {
        'search[url_ilike]': url.lower(),
        'only': 'url,artist',
        'limit': 1000,
    }
    data = danbooru_request(request_url, params)
    if data['error']:
        return data
    artists = [artist_url['artist'] for artist_url in data['json']]
    return {'error': False, 'artists': artists}


def get_artists_by_multiple_urls(url_list):
    request_url = '/artist_urls.json'
    params = {
        'search[url_matches]': ' '.join(url_list),
        'only': 'url,artist',
        'limit': 1000,
    }
    data = danbooru_request(request_url, params, long=True)
    if data['error']:
        return data
    retdata = {}
    for artist_url in data['json']:
        add_dict_entry(retdata, artist_url['url'], artist_url['artist'])
    return {'error': False, 'data': retdata}


def get_danbooru_posts_by_md5s(md5_list):
    request_url = '/posts.json'
    params = {
        'tags': 'md5:' + ','.join(md5_list),
        'limit': 200,  # Maximum number of posts
    }
    method = 'get'
    if len(md5_list) > 100:
        params['_method'] = 'get'
        method = 'post'
    all_posts = []
    while True:
        data = danbooru_request(request_url, params, method=method)
        if data['error']:
            return data
        posts = [post for post in data['json'] if 'md5' in post]
        all_posts.extend(posts)
        if len(data['json']) < 200:
            break
        params['page'] = 'b' + str(min(post['id'] for post in posts))
    return {'error': False, 'posts': all_posts}


def get_uploads_by_md5(md5):
    request_url = '/uploads.json'
    params = {
        'search[uploader_name]': DANBOORU_USERNAME,
        'search[upload_media_assets][media_asset][md5]': md5,
        'only': 'id,source,media_assets[md5]',
    }
    data = danbooru_request(request_url, params)
    if data['error']:
        return data
    uploads = [upload for upload in data['json'] if
               any(asset for asset in upload['media_assets'] if asset['md5'] == md5)]
    return {'error': False, 'uploads': uploads}


def create_upload_from_buffer(buffer, filename, mimetype):
    request_url = '/uploads.json'
    files = {
        'upload[files][0]': (filename, buffer, mimetype),
    }
    data = danbooru_request(request_url, files=files, method='post')
    if data['error']:
        return data
    return {'error': False, 'upload': data['json']}
