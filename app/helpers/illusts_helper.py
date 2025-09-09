# APP/HELPERS/ILLUSTS_HELPERS.PY

# ## PYTHON IMPORTS
import urllib.parse

# ## EXTERNAL IMPORTS
from flask import url_for, request

# ## PACKAGE IMPORTS
from config import DANBOORU_HOSTNAME

# ## LOCAL IMPORTS
from ..logical.utility import search_url_for
from .base_helper import external_link, general_link, put_link, delete_link, post_link


# ## FUNCTIONS

# #### URL functions

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
    if illust.site_name == 'custom':
        url = illust.site_url
    else:
        url = illust.secondary_url or illust.primary_url
    query_string = urllib.parse.urlencode({'url': url})
    return external_link("Danbooru", DANBOORU_HOSTNAME + '/uploads/batch?' + query_string)


def update_from_source_link(illust):
    return post_link("Update from source", url_for('illust.query_update_html', id=illust.id))


def add_media_url_link(illust):
    return general_link("+", url_for('illust_url.new_html', illust_id=illust.id))


def add_commentary_link(illust):
    addons = {'prompt': "Enter the site illust URL of commentary:", 'prompt-arg': 'url'}
    return post_link("+", url_for('illust.create_commentary_from_source', id=illust.id), **addons)


def update_artist_link(illust):
    addons = {'prompt': "Enter the artist ID:", 'prompt-arg': 'artist_id'}
    return post_link("change", url_for('illust.update_artist_html', id=illust.id), **addons)


def delete_title_link(illust, title):
    return delete_link("remove", url_for('illust.delete_title_html', id=illust.id, description_id=title.id))


def swap_title_link(illust, title):
    return put_link("swap", url_for('illust.swap_title_html', id=illust.id, description_id=title.id))


def delete_commentary_link(illust, commentary, relation):
    return delete_link("remove", url_for('illust.delete_commentary_html', id=illust.id,
                                         description_id=commentary.id, relation=relation))


def swap_commentary_link(illust, commentary):
    return put_link("swap", url_for('illust.swap_commentary_html', id=illust.id, description_id=commentary.id))


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
    return external_link(illust.sitelink, illust.primary_url)


def alt_site_illust_link(illust):
    secondary_url = illust.secondary_url
    return external_link('»', secondary_url) if secondary_url is not None else ""
