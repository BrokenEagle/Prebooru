# APP/CONTROLLERS/PROXY_CONTROLLER.PY

# ## PYTHON IMPORTS
import requests
from bs4 import BeautifulSoup

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, Markup, jsonify

# ## PACKAGE IMPORTS
from config import DANBOORU_USERNAME, DANBOORU_APIKEY, DANBOORU_HOSTNAME
from utility.file import put_get_raw

# ## LOCAL IMPORTS
from ..models import Post
from ..logical.sources.base import get_source_by_id
from ..logical.sources.danbooru import get_uploads_by_md5, create_upload_from_buffer


# ## GLOBAL VARIABLES

bp = Blueprint("proxy", __name__)

MIMETYPES = {
    'jpg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',
    'mp4': 'video/mp4',
}


# ## FUNCTIONS

# #### Helper functions

def _cors_json(json):
    response = jsonify(json)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


def error_resp(message):
    return _cors_json({'error': True, 'message': message})


# #### Auxiliary functions

def create_upload(post):
    buffer = put_get_raw(post.file_path, 'rb')
    filename = post.md5 + '.' + post.file_ext
    mimetype = MIMETYPES[post.file_ext]
    data = create_upload_from_buffer(buffer, filename, mimetype)
    if data['error']:
        return data
    return {'error': False, 'uploads': [data['upload']]}


# #### Route functions

# ###### Danbooru uploads proxy

@bp.route('/proxy/danbooru_upload_data.json', methods=['POST'])
def danbooru_upload_data():
    """Get data that can be used to populate the Danbooru new uploads page."""
    post_id = request.values.get('post_id', type=int)
    if post_id is None:
        return error_resp("Must include post ID.")
    post = Post.find(post_id)
    if post is None:
        return error_resp("Post #d not found." % post_id)
    if len(post.illusts) > 1:
        illust_id = request.values.get('illust_id', type=int)
        if illust_id is None:
            return error_resp("Ambiguous illustrations. Must include illust ID.")
        illust = next(filter(lambda x: x.id == illust_id, post.illusts), None)
        if illust is None:
            return error_resp("Illust #%d not on post #%d." % (post_id, illust_id))
    else:
        illust = post.illusts[0]
    source = get_source_by_id(illust.site_id)
    post_url = source.get_post_url(illust)
    profile_urls = source.artist_profile_urls(illust.artist)
    illust_commentaries = source.illust_commentaries_dtext(illust)
    tags = source.BAD_ID_TAGS.copy() if not illust.active or not illust.artist.active else []
    tags += ['inactive_account'] if not illust.artist.active else []
    tags += list(set([booru.current_name for booru in illust.artist.boorus]))
    return _cors_json({'error': False, 'post_url': post_url, 'tags': tags, 'post': post.to_json(),
                       'profile_urls': profile_urls, 'illust_commentaries': illust_commentaries,
                       'illust': illust.to_json(), 'artist': illust.artist.to_json()})


@bp.route('/proxy/danbooru_preprocess_upload.json', methods=['POST'])
def danbooru_preprocess_upload():
    """Send the local post file to Danbooru for preprocessing."""
    post_id = request.values.get('post_id', type=int)
    if post_id is None:
        return error_resp("Must include post ID.")
    post = Post.find(post_id)
    if post is None:
        return error_resp("Post #d not found." % post_id)
    upload_ret = get_uploads_by_md5(post.md5)
    if upload_ret['error']:
        return _cors_json(upload_ret)
    if len(upload_ret['uploads']) == 0:
        upload_ret = create_upload(post)
        if upload_ret['error']:
            return _cors_json(upload_ret)
    # Preference for uploads created via file upload
    upload = next(filter(lambda x: x['source'] is None, upload_ret['uploads']), None)
    upload = upload or upload_ret['uploads'][0]
    return _cors_json({'error': False, 'upload': upload})


# ###### Similarity sites proxy

@bp.route('/proxy/danbooru_iqdb', methods=['GET'])
def danbooru_iqdb():
    post_id = request.args.get('post_id', type=int)
    if post_id is None:
        return "Must include post ID."
    post = Post.find(post_id)
    if post is None:
        return "Post #d not found." % post_id
    file_path = post.file_path if post.file_ext != 'mp4' else post.sample_path
    buffer = put_get_raw(file_path, 'rb')
    files = {
        'search[file]': buffer,
    }
    resp = requests.post(DANBOORU_HOSTNAME + '/iqdb_queries', files=files, auth=(DANBOORU_USERNAME, DANBOORU_APIKEY))
    if resp.status_code != 200:
        return "HTTP Error %d: %s" % (resp.status_code, resp.reason)
    soup = BeautifulSoup(resp.text, 'lxml')
    base = soup.new_tag("base")
    base['href'] = DANBOORU_HOSTNAME
    soup.head.insert(0, base)
    return Markup(soup.prettify())


@bp.route('/proxy/saucenao', methods=['GET'])
def saucenao():
    post_id = request.args.get('post_id', type=int)
    if post_id is None:
        return "Must include post ID."
    post = Post.find(post_id)
    if post is None:
        return "Post #d not found." % post_id
    file_path = post.file_path if post.file_ext != 'mp4' else post.sample_path
    buffer = put_get_raw(file_path, 'rb')
    files = {
        'file': buffer,
    }
    resp = requests.post('https://saucenao.com/search.php', files=files)
    if resp.status_code != 200:
        return "HTTP Error %d: %s" % (resp.status_code, resp.reason)
    soup = BeautifulSoup(resp.text, 'lxml')
    base = soup.new_tag("base")
    base['href'] = 'https://saucenao.com'
    soup.head.insert(0, base)
    return Markup(soup.prettify())


@bp.route('/proxy/ascii2d', methods=['GET'])
def ascii2d():
    post_id = request.args.get('post_id', type=int)
    if post_id is None:
        return "Must include post ID."
    post = Post.find(post_id)
    if post is None:
        return "Post #d not found." % post_id
    file_path = post.file_path if post.file_ext != 'mp4' else post.sample_path
    buffer = put_get_raw(file_path, 'rb')
    filename = post.md5 + '.' + post.file_ext
    files = {
        'file': (filename, buffer, 'application/octet-stream')
    }
    resp = requests.post('https://ascii2d.net/search/file', files=files)
    if resp.status_code != 200:
        return "HTTP Error %d: %s" % (resp.status_code, resp.reason)
    soup = BeautifulSoup(resp.text, 'lxml')
    base = soup.new_tag("base")
    base['href'] = 'https://ascii2d.net'
    soup.head.insert(0, base)
    return Markup(soup.prettify())
