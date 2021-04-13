# APP/MODELS/ARTISTS_HELPER.PY

# ## PYTHON IMPORTS
from flask import Markup

# ## LOCAL IMPORTS
from ..sites import GetSiteKey
from ..sources import SOURCEDICT
from .base_helper import SearchUrlFor, ExternalLink


# ## FUNCTIONS


def ShortLink(artist):
    site_key = GetSiteKey(artist.site_id)
    source = SOURCEDICT[site_key]
    return source.ARTIST_SHORTLINK % artist.site_artist_id


def HrefUrl(artist):
    site_key = GetSiteKey(artist.site_id)
    source = SOURCEDICT[site_key]
    return source.ARTIST_HREFURL % artist.site_artist_id


def PostSearch(artist):
    return SearchUrlFor('post.index_html', illust_urls={'illust': {'artist_id': artist.id}})


def IllustSearch(artist):
    return SearchUrlFor('illust.index_html', artist_id=artist.id)


def MainUrl(artist):
    site_key = GetSiteKey(artist.site_id)
    source = SOURCEDICT[site_key]
    return source.ArtistMainUrl(artist)


def MediaUrl(artist):
    site_key = GetSiteKey(artist.site_id)
    source = SOURCEDICT[site_key]
    return source.ArtistMediaUrl(artist)


def LikesUrl(artist):
    site_key = GetSiteKey(artist.site_id)
    source = SOURCEDICT[site_key]
    return source.ArtistLikesUrl(artist)


# #### Link functions

def WebpageLink(url):
    return ExternalLink(url, url)


def SiteArtistLink(artist):
    return ExternalLink(ShortLink(artist), HrefUrl(artist))


def ArtistLinks(artist):
    site_key = GetSiteKey(artist.site_id)
    source = SOURCEDICT[site_key]
    if not source.HasArtistUrls(artist):
        return Markup('<em>N/A</em>')
    all_links = [ExternalLink(name.title(), url) for (name, url) in source.ArtistLinks(artist).items()]
    return Markup(' | '.join(all_links))
