# APP/HELPERS/POSTS_HELPER.PY

# ## PYTHON IMPORTS
import urllib.parse

# ## EXTERNAL IMPORTS
from flask import Markup, url_for, request

# ## PACKAGE IMPORTS
from config import DANBOORU_HOSTNAME
from utility.data import readable_bytes

# ## LOCAL IMPORTS
from ..logical.utility import search_url_for
from ..logical.sources.base import get_source_by_id
from .base_helper import general_link, external_link, url_for_with_params


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
        source = get_source_by_id(illust_url.site_id)
        media_url = source.get_media_url(illust_url)
        if source.is_video_url(media_url):
            small_url = source.get_sample_url(illust_url)
        else:
            small_url = source.small_image_url(media_url)
        encoded_url = urllib.parse.quote_plus(small_url)
        href_url = format_url + encoded_url
        image_links.append(external_link(illust.shortlink, href_url))
    return Markup(' | ').join(image_links)


def image_title(post):
    return f"( {post.width} x {post.height} ) : {post.file_ext.upper()} @ {readable_bytes(post.size)}"


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
            url = DANBOORU_HOSTNAME + f'/uploads/new?prebooru_post_id={post.id}&prebooru_illust_id={illust.id}'
            image_links.append(external_link(f'file #{illust.id}', url))
            continue
        source = get_source_by_id(illust_url.site_id)
        media_url = source.get_media_url(illust_url)
        post_url = source.get_post_url(illust)
        query_string = urllib.parse.urlencode({'url': media_url, 'ref': post_url})
        href_url = DANBOORU_HOSTNAME + '/uploads/new?' + query_string
        image_links.append(external_link(illust.shortlink, href_url))
    return Markup(' | ').join(image_links)


def regenerate_previews_link(post):
    url = url_for('post.regenerate_previews_html', id=post.id)
    addons = {'onclick': "return Posts.regeneratePreviews(this)"}
    return general_link("Regenerate previews", url, **addons)


def regenerate_similarity_link(post):
    url = url_for('similarity.regenerate_html', post_id=post.id)
    addons = {'onclick': "return Posts.regenerateSimilarity(this)"}
    return general_link("Regenerate similarity", url, **addons)


def disk_file_link(post):
    addons = {'onclick': 'return Posts.copyFileLink(this)', 'data-file-path': post.file_path}
    return general_link("Copy file link", "#", **addons)


def add_notation_link(post):
    return general_link("Add notation", url_for('notation.new_html', post_id=post.id))


def add_tag_link(post):
    addons = {'onclick': "return Prebooru.addTag(this, 'post')", 'data-post-id': post.id}
    return general_link("Add tag", url_for('tag.append_item_index_html'), **addons)


def add_to_pool_link(post):
    addons = {'onclick': "return Prebooru.createPool(this, 'post')", 'data-post-id': post.id}
    return general_link("Add to pool", url_for('pool_element.create_html'), **addons)


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
