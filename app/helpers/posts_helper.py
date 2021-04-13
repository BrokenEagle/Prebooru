# APP/HELPERS/POSTS_HELPER.PY

# ##PYTHON IMPORTS
from flask import Markup, url_for
import urllib.parse

# ##LOCAL IMPORTS
from ..sources.base_source import GetSourceById
from .base_helper import SearchUrlFor, GeneralLink, ExternalLink


# ## GLOBAL VARIABLES

DANBOORU_UPLOAD_LINK = 'https://danbooru.donmai.us/uploads/new?prebooru_post_id='


# ## FUNCTIONS

def SimilarSearchLinks(post, format_url, proxy_url=None):
    image_links = []
    for i in range(0, len(post.illust_urls)):
        illust_url = post.illust_urls[i]
        illust = illust_url.illust
        if not illust.active:
            continue
        source = GetSourceById(illust_url.site_id)
        media_url = source.GetMediaUrl(illust_url)
        if source.IsVideoUrl(media_url):
            _, thumb_illust_url = source.VideoIllustDownloadUrls(illust)
            small_url = source.GetMediaUrl(thumb_illust_url)
        else:
            small_url = source.SmallImageUrl(media_url)
        encoded_url = urllib.parse.quote_plus(small_url)
        href_url = format_url + encoded_url
        image_links.append(ExternalLink(illust.shortlink, href_url))
    if len(image_links) == 0:
        if proxy_url is not None:
            image_links.append(ExternalLink('file', proxy_url + '?post_id=' + str(post.id)))
        else:
            image_links.append('N/A')
    return Markup(' | ').join(image_links)


def DanbooruSearchLinks(post):
    return SimilarSearchLinks(post, 'https://danbooru.donmai.us/iqdb_queries?url=', '/proxy/danbooru_iqdb')


def SauceNAOSearchLinks(post):
    return SimilarSearchLinks(post, 'https://saucenao.com/search.php?db=999&url=', '/proxy/saucenao')


def Ascii2DSearchLinks(post):
    return SimilarSearchLinks(post, 'https://ascii2d.net/search/url/', '/proxy/ascii2d')


def IQDBOrgSearchLinks(post):
    return SimilarSearchLinks(post, 'https://iqdb.org/?url=')


def DanbooruPostBookmarkletLinks(post):
    image_links = []
    for i in range(0, len(post.illust_urls)):
        illust_url = post.illust_urls[i]
        illust = illust_url.illust
        if not illust.active:
            continue
        source = GetSourceById(illust_url.site_id)
        media_url = source.GetMediaUrl(illust_url)
        post_url = source.GetPostUrl(illust)
        query_string = urllib.parse.urlencode({'url': media_url, 'ref': post_url})
        href_url = 'https://danbooru.donmai.us/uploads/new?' + query_string
        image_links.append(ExternalLink(illust.shortlink, href_url))
    if len(image_links) == 0:
        image_links.append(ExternalLink('file', DANBOORU_UPLOAD_LINK + str(post.id)))
    return Markup(' | ').join(image_links)


def RegenerateSimilarityLink(post):
    return GeneralLink("Regenerate similarity", url_for('post.regenerate_html', id=post.id), **{'onclick': "return Post.regenerateSimilarity(this)"})


def FileLink(post):
    return GeneralLink("Copy file link", "#", **{'onclick': 'return Posts.copyFileLink(this)', 'data-file-path': post.file_path})


def AddNotationLink(post):
    return GeneralLink("Add notation", url_for('notation.new_html', post_id=post.id))


def AddToPoolLink(post):
    return GeneralLink("Add to pool", url_for('pool_element.create_html'), **{'onclick': "return Prebooru.createPool(this, 'post')", 'data-post-id': post.id})


def RelatedPostsSearch(post):
    illust_ids_str = ','.join([str(illust.id) for illust in post.illusts])
    return SearchUrlFor('post.index_html', illust_urls={'illust_id': illust_ids_str})


def SimilarityPostPoolLink(post):
    return GeneralLink(post.similar_post_count, url_for('similarity_pool.show_html', id=post.similar_pool_id))


def SimilaritySiblingPoolLink(post_data):
    return GeneralLink(post_data.post.shortlink, url_for('similarity_pool.show_html', id=post_data.element.sibling.pool_id)) if post_data.element.sibling is not None else "Sibling missing"


def DeleteSimilarityElementLink(element):
    return GeneralLink("remove", element.delete_url, **{'onclick': 'return SimilarityPosts.deleteElement(this)', 'class': 'warning-link'})
