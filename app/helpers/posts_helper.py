# APP/HELPERS/POSTS_HELPER.PY

# ## PYTHON IMPORTS
import math
import urllib.parse

# ## EXTERNAL IMPORTS
from flask import Markup, url_for, request

# ## PACKAGE IMPORTS
from config import DANBOORU_HOSTNAME, SAMPLE_DIMENSIONS, PREVIEW_DIMENSIONS, PREBOORU_PORT
from utility.data import readable_bytes

# ## LOCAL IMPORTS
from .. import SERVER_INFO
from ..logical.utility import search_url_for
from .base_helper import general_link, external_link, url_for_with_params, render_tag, get_preview_dimensions


# ## GLOBAL VARIABLES

VIDEO_PICTURE = """
<picture style="position: relative; width: %dpx; height: %dpx;">
    %s
    %s
</picture>
"""


# ## FUNCTIONS

# #### URL functions

def related_posts_search(post):
    illust_ids_str = ','.join([str(illust.id) for illust in post.illusts])
    return search_url_for('post.index_html', illust_urls={'illust_id': illust_ids_str})


# #### Link functions

# ###### GENERAL

def similar_search_links(post, format_url, proxy_url=None):
    image_links = []
    for i in range(0, len(post.illust_urls)):
        illust_url = post.illust_urls[i]
        illust = illust_url.illust
        artist = illust.artist
        if not illust.active or not artist.active:
            if proxy_url is not None:
                image_links.append(external_link(f'file #{illust.id}', proxy_url + '?post_id=' + str(post.id)))
            else:
                image_links.append('N/A')
            continue
        source = illust.site.source
        media_url = illust_url.full_url
        if source.is_video_url(media_url):
            small_url = illust_url.full_sample_url
        else:
            small_url = illust_url.full_preview_url
        encoded_url = urllib.parse.quote_plus(small_url)
        href_url = format_url + encoded_url
        image_links.append(external_link(illust.shortlink, href_url))
    return Markup(' | ').join(image_links)


def post_preview_link(post, lazyload):
    preview_width, preview_height = get_preview_dimensions(post.width, post.height, PREVIEW_DIMENSIONS)
    addons = {
        'class': 'preview',
        'width': preview_width,
        'height': preview_height,
        'alt': post.shortlink,
        'title': image_title(post),
        'onerror': 'Prebooru.onImageError(this)',
        'data-src': post.preview_url,
    }
    if not lazyload:
        addons['src'] = post.preview_url
    if post.media.is_video:
        addons['data-video'] = post.video_preview_url
    return render_tag('img', None, addons)


def image_sample_link(post, class_=None):
    sample_width, sample_height = get_preview_dimensions(post.width, post.height, SAMPLE_DIMENSIONS)
    addons = {
        'width': sample_width,
        'height': sample_height,
        'alt': post.shortlink,
        'title': image_title(post),
        'src': post.sample_url,
        'onerror': 'Prebooru.onImageError(this)',
    }
    if class_ is not None:
        addons['class'] = class_
    return render_tag('img', None, addons)


def video_picture_link(post):
    sample_link = image_sample_link(post, class_='thumbnail')
    return Markup(VIDEO_PICTURE % (post.width, post.height, sample_link, _play_icon_link()))


def video_sample_link(post):
    video_url = post.video_sample_url if post.video_sample_exists else post.file_url
    original_url = post.file_url if post.video_sample_exists else None
    addons = {
        'controls': None,
        'autoplay': None,
        'width': post.width,
        'height': post.height,
        'duration': post.duration,
        'title': image_title(post),
        'data-src': video_url,
        'data-original': original_url,
    }
    return render_tag('video', True, addons)


def image_title(post):
    title = f"( {post.width} x {post.height} )"
    if post.duration is not None:
        title += f" [ {round(post.duration, 1)} sec ]"
    return title + f" : {post.file_ext.upper()} @ {readable_bytes(post.size)}"


# ###### SHOW

def danbooru_search_links(post):
    return similar_search_links(post, DANBOORU_HOSTNAME + '/iqdb_queries?url=', '/proxy/danbooru_iqdb')


def saucenao_search_links(post):
    return similar_search_links(post, 'https://saucenao.com/search.php?db=999&url=', '/proxy/saucenao')


def ascii2d_search_links(post):
    return similar_search_links(post, 'https://ascii2d.net/search/url/')


def iqdborg_search_links(post):
    return similar_search_links(post, 'https://iqdb.org/?url=')


def danbooru_post_bookmarklet_links(post):
    image_links = []
    for i in range(0, len(post.illust_urls)):
        illust_url = post.illust_urls[i]
        illust = illust_url.illust
        artist = illust.artist
        if not illust.active or not artist.active:
            url_parameters = f'prebooru_post_id={post.id}&' +\
                             f'prebooru_illust_id={illust.id}&' +\
                             f'prebooru_server={SERVER_INFO.addr}:{PREBOORU_PORT}'
            url = DANBOORU_HOSTNAME + '/uploads/new?' + url_parameters
            image_links.append(external_link(f'file #{illust.id}', url))
            continue
        source = illust.site.source
        media_url = illust_url.full_url
        post_url = source.get_post_url(illust)
        query_string = urllib.parse.urlencode({'url': media_url, 'ref': post_url})
        href_url = DANBOORU_HOSTNAME + '/uploads/new?' + query_string
        image_links.append(external_link(illust.shortlink, href_url))
    return Markup(' | ').join(image_links)


def regenerate_previews_link(post):
    url = url_for('post.regenerate_previews_html', id=post.id)
    addons = {'onclick': "return Posts.regeneratePreviews(this)"}
    return general_link("Regenerate previews", url, **addons)


def regenerate_image_matches_link(post):
    url = url_for('image_hash.regenerate_html', post_id=post.id)
    addons =\
        {
            'onclick': "return Posts.regenerateImageMatches(this)",
            'title': "Will regenerate the image signatures used to match against other images.",
        }
    return general_link("Regenerate image matches", url, **addons)


def disk_file_link(post):
    addons = {'onclick': 'return Posts.copyFileLink(this)', 'data-file-path': post.file_path}
    return general_link("Copy file link", "#", **addons)


def add_notation_link(post):
    return general_link("Add notation", url_for('notation.new_html', post_id=post.id, redirect='true'))


def add_tag_link(post):
    url = url_for('tag.append_item_index_json', preview='true')
    addons = {'onclick': "return Prebooru.addTag(this, 'post')", 'data-post-id': post.id}
    return general_link("Add tag", url, **addons)


def add_to_pool_link(post):
    url = url_for('pool_element.create_json', preview='true')
    addons = {
        'onclick': "return Pools.createElement(this, 'post')",
        'data-post-id': post.id,
    }
    return general_link("Add to pool", url, **addons)


def danbooru_post_link(post):
    if post.danbooru_id is not None:
        return external_link('#%d' % post.danbooru_id, DANBOORU_HOSTNAME + '/posts/%d' % post.danbooru_id)
    return Markup('<em>N/A</em>')


# ###### INDEX

def post_type_link(post_type):
    active_type = request.args.get('type') or 'all'
    classes = ['post-type'] + [post_type + '-type'] + (['type-active'] if active_type == post_type else [])
    return general_link(post_type.title(), url_for_with_params('post.index_html', type=post_type, page=None),
                        **{'class': ' '.join(classes)})


# #### Other functions

def video_icons(post):
    duration = math.ceil(post.duration)
    minutes = duration // 60
    seconds = duration % 60
    duration_string = "%d:%02d" % (minutes, seconds)
    inner_html = render_tag('span', duration_string, {'class': 'duration small-2'})
    if post.audio:
        inner_html += _sound_icon_link()
    return render_tag('div', inner_html, {'class': 'video-info'})


# #### Private functions

def _play_icon_link():
    addons = {
        'class': 'play-icon',
        'src': url_for('static', filename='play.svg'),
    }
    return render_tag('img', None, addons)


def _sound_icon_link():
    if not hasattr(_sound_icon_link, 'outer_html'):
        addons = {
            'class': 'sound-icon',
            'src': url_for('static', filename='sound.svg'),
        }
        setattr(_sound_icon_link, 'outer_html', render_tag('img', None, addons))
    return _sound_icon_link.outer_html
