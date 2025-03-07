# APP/HELPERS/ARTISTS_HELPER.PY

# ## EXTERNAL IMPORTS
from flask import Markup, url_for

# ## LOCAL IMPORTS
from ..models.model_enums import SiteDescriptor
from ..logical.utility import search_url_for
from .base_helper import general_link, external_link


# ## FUNCTIONS

# #### URL functions

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
    return general_link("Add notation", url_for('notation.new_html', artist_id=artist.id, redirect='true'))


def check_posts_link(artist):
    return general_link("Check posts", url_for('artist.check_posts_html', id=artist.id), method="POST")


def delete_account_link(artist, site_account):
    return general_link("remove", url_for('artist.delete_account_html', id=artist.id, label_id=site_account.id),
                        method="DELETE", **{'class': 'warning-link'})


def swap_account_link(artist, site_account):
    url = url_for('artist.swap_account_html', id=artist.id, label_id=site_account.id)
    return general_link("swap", url, method="PUT", **{'class': 'notice-link'})


def delete_name_link(artist, name):
    return general_link("remove", url_for('artist.delete_name_html', id=artist.id, label_id=name.id),
                        method="DELETE", **{'class': 'warning-link'})


def swap_name_link(artist, name):
    url = url_for('artist.swap_name_html', id=artist.id, label_id=name.id)
    return general_link("swap", url, method="PUT", **{'class': 'notice-link'})


def delete_profile_link(artist, profile):
    return general_link("remove", url_for('artist.delete_profile_html', id=artist.id, description_id=profile.id),
                        method="DELETE", **{'class': 'warning-link'})


def swap_profile_link(artist, profile):
    url = url_for('artist.swap_profile_html', id=artist.id, description_id=profile.id)
    return general_link("swap", url, method="PUT", **{'class': 'notice-link'})


def accounts_link(artist):
    return general_link("Accounts (%d)" % artist.site_accounts_count, url_for('artist.accounts_html', id=artist.id))


def names_link(artist):
    return general_link("Names (%d)" % artist.names_count, url_for('artist.names_html', id=artist.id))


def profiles_link(artist):
    return general_link("Profiles (%d)" % artist.profiles_count, url_for('artist.profiles_html', id=artist.id))


# ###### GENERAL

def post_search_link(artist):
    return general_link('»', post_search(artist))


def site_artist_link(artist):
    if artist.site_id == SiteDescriptor.custom.id:
        return Markup('N/A')
    return external_link(artist.sitelink, artist.primary_url)


def artist_links(artist):
    if artist.site_id == SiteDescriptor.custom.id:
        return Markup('N/A')
    source = artist.source
    if not source.has_artist_urls(artist):
        return Markup('<em>N/A</em>')
    all_links = [external_link(name.title(), url) for (name, url) in source.artist_links(artist).items()]
    return Markup(' | '.join(all_links))


def last_illust_info(artist):
    illust = artist.last_illust
    return (illust.site_illust_id, illust.site_created.isoformat())


def first_illust_info(artist):
    illust = artist.first_illust
    return (illust.site_illust_id, illust.site_created.isoformat())
