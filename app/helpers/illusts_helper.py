# APP/HELPERS/ILLUSTS_HELPERS.PY

# ##PYTHON IMPORTS
import urllib.parse
from flask import url_for

# ##LOCAL IMPORTS
from ..sites import GetSiteDomain, GetSiteKey
from ..sources import SOURCEDICT
from ..sources.base_source import GetSourceById
from .base_helper import SearchUrlFor, ExternalLink, UrlLink, GeneralLink


# ##GLOBAL VARIABLES

SITE_DATA_LABELS = {
    'site_updated': 'Updated',
    'site_uploaded': 'Uploaded',
}


# ##FUNCTIONS

# #### Form functions

def IsGeneralForm(form):
    return (form.artist_id.data is None) or (form.site_id.data is None)


def FormClass(form):
    CLASS_MAP = {
        None: "",
        1: "pixiv-data",
        3: "twitter-data",
    }
    return CLASS_MAP[form.site_id.data]


# #### Site content functions

def SiteMetricIterator(illust):
    site_data_json = illust.site_data.to_json()
    for key, val in site_data_json.items():
        if key in ['retweets', 'replies', 'quotes', 'bookmarks', 'views']:
            yield key, val


def SiteDateIterator(illust):
    site_data_json = illust.site_data.to_json()
    for key, val in site_data_json.items():
        if key in ['site_updated', 'site_uploaded']:
            yield SITE_DATA_LABELS[key], val


# #### Media functions

def IllustHasImages(illust):
    site_key = GetSiteKey(illust.site_id)
    source = SOURCEDICT[site_key]
    return source.IllustHasImages(illust)


def IllustHasVideos(illust):
    site_key = GetSiteKey(illust.site_id)
    source = SOURCEDICT[site_key]
    return source.IllustHasImages(illust)


def IllustUrlsOrdered(illust):
    return sorted(illust.urls, key=lambda x: x.order)


# #### URL functions

def OriginalUrl(illust_url):
    return UrlLink('https://' + GetSiteDomain(illust_url.site_id) + illust_url.url)


def ShortLink(illust):
    site_key = GetSiteKey(illust.site_id)
    return "%s #%d" % (site_key.lower(), illust.site_illust_id)


def SiteIllustUrl(illust):
    site_key = GetSiteKey(illust.site_id)
    source = SOURCEDICT[site_key]
    return source.GetIllustUrl(illust.site_illust_id)


def PostIllustSearch(illust):
    return SearchUrlFor('post.index_html', illust_urls={'illust_id': illust.id})


def PostTagSearch(tag):
    return SearchUrlFor('post.index_html', illust_urls={'illust': {'tags': {'name': tag.name}}})


def DanbooruBatchUrl(illust):
    source = GetSourceById(illust.site_id)
    post_url = source.GetPostUrl(illust)
    query_string = urllib.parse.urlencode({'url': post_url})
    return 'https://danbooru.donmai.us/uploads/batch?' + query_string


# #### Link functions

def DanbooruUploadLink(illust):
    return ExternalLink("Danbooru", DanbooruBatchUrl(illust))


def UpdateFromSourceLink(illust):
    return GeneralLink("Update from source", url_for('illust.query_update_html', id=illust.id), **{'onclick': "return Prebooru.linkPost(this)"})


def AddMediaUrlLink(illust):
    return GeneralLink("Add media url", url_for('illust_url.new_html', illust_id=illust.id))


def AddNotationLink(illust):
    return GeneralLink("Add notation", url_for('notation.new_html', illust_id=illust.id))


def AddPoolLink(illust):
    return GeneralLink("Add pool", url_for('pool_element.create_html'), **{'onclick': "return Prebooru.createPool(this, 'illust')", 'data-illust-id': illust.id})


def SiteIllustLink(illust):
    return ExternalLink(ShortLink(illust), SiteIllustUrl(illust))


def PostIllustLink(illust):
    site_key = GetSiteKey(illust.site_id)
    source = SOURCEDICT[site_key]
    post_url = source.GetPostUrl(illust)
    return ExternalLink('&raquo;', post_url) if post_url != source.GetIllustUrl(illust.site_illust_id) else ""
