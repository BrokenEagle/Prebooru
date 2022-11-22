# APP/HELPERS/ARTISTS_HELPER.PY

# ## EXTERNAL IMPORTS
from flask import Markup, url_for

# ## LOCAL IMPORTS
from ..logical.utility import search_url_for
from ..logical.sites import SiteDescriptor
from .base_helper import general_link, external_link


# ## FUNCTIONS

# #### URL functions

def site_short_link(artist):
    return artist.site.source.ARTIST_SHORTLINK % artist.site_artist_id


def href_url(artist):
    return artist.site.source.ARTIST_HREFURL % artist.site_artist_id


def post_search(artist):
    return search_url_for('post.index_html', illust_urls={'illust': {'artist_id': artist.id}})


def illust_search(artist):
    return search_url_for('illust.index_html', artist_id=artist.id)


# #### Link functions

# ###### SHOW

def query_update_link(artist):
    return general_link("Update from source", url_for('artist.query_update_html', id=artist.id), method="POST")


def query_booru_link(artist):
    return general_link("Query for booru", url_for('artist.query_booru_html', id=artist.id), method="POST")


def add_illust_link(artist):
    return general_link("Add illust", url_for('illust.new_html', artist_id=artist.id))


def add_subscription_link(artist):
    return general_link("Add subscription", url_for('subscription.new_html', artist_id=artist.id))


def add_notation_link(artist):
    return general_link("Add notation", url_for('notation.new_html', artist_id=artist.id))


def delete_profile_link(artist, profile):
    return general_link("remove", url_for('artist.delete_profile_html', id=artist.id, description_id=profile.id),
                        method="DELETE", **{'class': 'warning-link'})


# ###### GENERAL

def post_search_link(artist):
    return general_link('»', post_search(artist))


def site_artist_link(artist):
    if artist.site == SiteDescriptor.CUSTOM:
        return Markup('N/A')
    return external_link(site_short_link(artist), href_url(artist))


def artist_links(artist):
    if artist.site == SiteDescriptor.CUSTOM:
        return Markup('N/A')
    source = artist.site.source
    if not source.has_artist_urls(artist):
        return Markup('<em>N/A</em>')
    all_links = [external_link(name.title(), url) for (name, url) in source.artist_links(artist).items()]
    return Markup(' | '.join(all_links))
