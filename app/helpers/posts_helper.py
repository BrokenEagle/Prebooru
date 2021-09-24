# APP/HELPERS/POSTS_HELPER.PY

# ##PYTHON IMPORTS
from flask import Markup, url_for
import urllib.parse

# ##LOCAL IMPORTS
from ..logical.sources.base import get_source_by_id
from .base_helper import search_url_for, general_link, external_link
from ..config import DANBOORU_HOSTNAME


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
        if not illust.active:
            continue
        source = get_source_by_id(illust_url.site_id)
        media_url = source.get_media_url(illust_url)
        if source.is_video_url(media_url):
            _, thumb_illust_url = source.VideoIllustDownloadUrls(illust)
            small_url = source.get_media_url(thumb_illust_url)
        else:
            small_url = source.small_image_url(media_url)
        encoded_url = urllib.parse.quote_plus(small_url)
        href_url = format_url + encoded_url
        image_links.append(external_link(illust.shortlink, href_url))
    if len(image_links) == 0:
        if proxy_url is not None:
            image_links.append(external_link('file', proxy_url + '?post_id=' + str(post.id)))
        else:
            image_links.append('N/A')
    return Markup(' | ').join(image_links)


# ###### SHOW

def danbooru_search_links(post):
    return similar_search_links(post, DANBOORU_HOSTNAME + '/iqdb_queries?url=', '/proxy/danbooru_iqdb')


def saucenao_search_links(post):
    return similar_search_links(post, 'https://saucenao.com/search.php?db=999&url=', '/proxy/saucenao')


def ascii2d_search_links(post):
    return similar_search_links(post, 'https://ascii2d.net/search/url/', '/proxy/ascii2d')


def iqdborg_search_links(post):
    return similar_search_links(post, 'https://iqdb.org/?url=')


def danbooru_post_bookmarklet_links(post):
    image_links = []
    for i in range(0, len(post.illust_urls)):
        illust_url = post.illust_urls[i]
        illust = illust_url.illust
        if not illust.active:
            continue
        source = get_source_by_id(illust_url.site_id)
        media_url = source.get_media_url(illust_url)
        post_url = source.get_post_url(illust)
        query_string = urllib.parse.urlencode({'url': media_url, 'ref': post_url})
        href_url = DANBOORU_HOSTNAME + '/uploads/new?' + query_string
        image_links.append(external_link(illust.shortlink, href_url))
    if len(image_links) == 0:
        image_links.append(external_link('file', DANBOORU_HOSTNAME + '/uploads/new?prebooru_post_id=%d' % post.id))
    return Markup(' | ').join(image_links)


def regenerate_similarity_link(post):
    return general_link("Regenerate similarity", url_for('similarity.regenerate_html', post_id=post.id), **{'onclick': "return Posts.regenerateSimilarity(this)"})


def disk_file_link(post):
    return general_link("Copy file link", "#", **{'onclick': 'return Posts.copyFileLink(this)', 'data-file-path': post.file_path})


def add_notation_link(post):
    return general_link("Add notation", url_for('notation.new_html', post_id=post.id))


def add_to_pool_link(post):
    return general_link("Add to pool", url_for('pool_element.create_html'), **{'onclick': "return Prebooru.createPool(this, 'post')", 'data-post-id': post.id})


def danbooru_post_link(post):
    return external_link('#%d' % post.danbooru_id, DANBOORU_HOSTNAME + '/posts/%d' % post.danbooru_id) if post.danbooru_id is not None else Markup('<em>N/A</em>')

