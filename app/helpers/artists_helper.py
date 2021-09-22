# APP/MODELS/ARTISTS_HELPER.PY

# ## PYTHON IMPORTS
from flask import Markup

# ## LOCAL IMPORTS
from ..logical.sites import get_site_key
from ..sources import SOURCEDICT
from .base_helper import search_url_for, external_link


# ## FUNCTIONS


def short_link(artist):
    site_key = get_site_key(artist.site_id)
    source = SOURCEDICT[site_key]
    return source.ARTIST_SHORTLINK % artist.site_artist_id


def href_url(artist):
    site_key = get_site_key(artist.site_id)
    source = SOURCEDICT[site_key]
    return source.ARTIST_HREFURL % artist.site_artist_id


def post_search(artist):
    return search_url_for('post.index_html', illust_urls={'illust': {'artist_id': artist.id}})


def illust_search(artist):
    return search_url_for('illust.index_html', artist_id=artist.id)


def main_url(artist):  # Unused
    site_key = get_site_key(artist.site_id)
    source = SOURCEDICT[site_key]
    return source.artist_main_url(artist)


def media_url(artist):  # Unused
    site_key = get_site_key(artist.site_id)
    source = SOURCEDICT[site_key]
    return source.artist_media_url(artist)


def likes_url(artist):  # Unused
    site_key = get_site_key(artist.site_id)
    source = SOURCEDICT[site_key]
    return source.artist_likes_url(artist)


# #### Link functions

def webpage_link(url):
    return external_link(url, url)


def site_artist_link(artist):
    return external_link(short_link(artist), href_url(artist))


def artist_links(artist):
    site_key = get_site_key(artist.site_id)
    source = SOURCEDICT[site_key]
    if not source.has_artist_urls(artist):
        return Markup('<em>N/A</em>')
    all_links = [external_link(name.title(), url) for (name, url) in source.artist_links(artist).items()]
    return Markup(' | '.join(all_links))
