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


# ## GLOBAL VARIABLES

SITE_DATA_LABELS = {
    'site_updated': 'Updated',
    'site_uploaded': 'Uploaded',
}


# ## FUNCTIONS

# #### Form functions

def form_class(form):
    class_map = {
        None: "",
        site_descriptor.pixiv.id: "pixiv-data",
        site_descriptor.twitter.id: "twitter-data",
        site_descriptor.custom.id: "custom",
    }
    return class_map[form.site_id.data]


# #### Iterator functions

def site_metric_iterator(illust):
    if illust.site_id == site_descriptor.custom.id or illust.site_data is None:
        return
    site_data_json = illust.site_data.to_json()
    for key, val in site_data_json.items():
        if key in ['retweets', 'replies', 'quotes', 'bookmarks', 'views']:
            yield key, val


def site_date_iterator(illust):
    if illust.site_id == site_descriptor.custom.id or illust.site_data is None:
        return
    site_data_json = illust.site_data.to_json()
    for key, val in site_data_json.items():
        if key in ['site_updated', 'site_uploaded']:
            yield SITE_DATA_LABELS[key], val


# #### URL functions

def danbooru_batch_url(illust):
    query_string = urllib.parse.urlencode({'url': illust.secondary_url})
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


def delete_commentary_link(illust, commentary):
    url = url_for('illust.delete_commentary_html', id=illust.id, description_id=commentary.id)
    return general_link("remove", url, method="DELETE", **{'class': 'warning-link'})


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
