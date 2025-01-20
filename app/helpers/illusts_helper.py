# APP/HELPERS/ILLUSTS_HELPERS.PY

# ## PYTHON IMPORTS
import urllib.parse

# ## EXTERNAL IMPORTS
from flask import url_for, Markup, request

# ## PACKAGE IMPORTS
from config import DANBOORU_HOSTNAME

# ## LOCAL IMPORTS
from ..enum_imports import site_descriptor
from ..logical.utility import search_url_for
from .base_helper import external_link, general_link


# ## FUNCTIONS

# #### URL functions

def danbooru_batch_url(illust):
    url = illust.secondary_url or illust.primary_url
    query_string = urllib.parse.urlencode({'url': url})
    return DANBOORU_HOSTNAME + '/uploads/batch?' + query_string


def post_search(illust):
    return search_url_for('post.index_html', illust_urls={'illust_id': illust.id})


# #### Link functions

# ###### INDEX

def post_search_link(illust):
    return general_link('»', search_url_for('post.index_html', illust_urls={'illust_id': illust.id}))


def illust_url_search_link(illust, text):
    return general_link(text, search_url_for('illust_url.index_html', illust_id=illust.id))


# ###### SHOW

def danbooru_upload_link(illust):
    if illust.site_id == site_descriptor.custom.id:
        return Markup("N/A")
    return external_link("Danbooru", danbooru_batch_url(illust))


def update_from_source_link(illust):
    url = url_for('illust.query_update_html', id=illust.id)
    addons = {'onclick': "return Prebooru.linkPost(this)"}
    return general_link("Update from source", url, **addons)


def add_media_url_link(illust):
    return general_link("Add media url", url_for('illust_url.new_html', illust_id=illust.id))


def add_notation_link(illust):
    return general_link("Add notation", url_for('notation.new_html', illust_id=illust.id, redirect='true'))


def add_commentary_link(illust):
    url = url_for('illust.create_commentary_from_source', id=illust.id)
    addons = {'onclick': "return Illusts.createCommentary(this)"}
    return general_link("Add commentary", url, **addons)


def add_pool_link(illust):
    url = url_for('pool_element.create_json', preview='true')
    addons = {
        'onclick': "return Pools.createElement(this, 'illust')",
        'data-illust-id': illust.id,
    }
    return general_link("Add to pool", url, **addons)


def update_artist_link(illust):
    url = url_for('illust.update_artist_html', id=illust.id)
    addons = {'onclick': "return Illusts.updateArtist(this)"}
    return general_link("Update artist", url, **addons)


def delete_title_link(illust, title):
    url = url_for('illust.delete_title_html', id=illust.id, description_id=title.id)
    return general_link("remove", url, method="DELETE", **{'class': 'warning-link'})


def swap_title_link(illust, title):
    url = url_for('illust.swap_title_html', id=illust.id, description_id=title.id)
    return general_link("swap", url, method="PUT", **{'class': 'notice-link'})


def delete_commentary_link(illust, commentary, relation):
    url = url_for('illust.delete_commentary_html', id=illust.id, description_id=commentary.id, relation=relation)
    return general_link("remove", url, method="DELETE", **{'class': 'warning-link'})


def swap_commentary_link(illust, commentary):
    url = url_for('illust.swap_commentary_html', id=illust.id, description_id=commentary.id)
    return general_link("swap", url, method="PUT", **{'class': 'notice-link'})


def urls_navigation_link(illust, url_type):
    text = url_type
    active_type = request.args.get('urls')
    url = illust.show_url
    if url_type != 'all':
        url += '?urls=' + url_type
    else:
        url_type = None
    addons = {'class': 'type-active'} if url_type == active_type else {}
    return general_link(text, url, **addons)


def titles_link(illust):
    url = url_for('illust.titles_html', id=illust.id)
    return general_link("Titles (%d)" % illust.titles_count, url)


def commentaries_link(illust):
    url = url_for('illust.commentaries_html', id=illust.id)
    return general_link("Commentaries (%d)" % illust.commentaries_count, url)


# ###### GENERAL

def site_illust_link(illust):
    if illust.site_id == site_descriptor.custom.id:
        # Need to add a post_url for CustomData, a subclass for SiteData
        return Markup("N/A")
    return external_link(illust.sitelink, illust.primary_url)


def alt_site_illust_link(illust):
    if illust.site_id == site_descriptor.custom.id:
        return ""
    secondary_url = illust.secondary_url
    return external_link('»', secondary_url) if secondary_url is not None else ""
