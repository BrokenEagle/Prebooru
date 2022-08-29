# APP/HELPERS/ILLUSTS_HELPERS.PY

# ## PYTHON IMPORTS
import urllib.parse

# ## EXTERNAL IMPORTS
from flask import url_for

# ## PACKAGE IMPORTS
from config import DANBOORU_HOSTNAME

# ## LOCAL IMPORTS
from ..logical.utility import search_url_for
from ..logical.sites import get_site_key
from ..logical.sources import SOURCEDICT
from ..logical.sources.base import get_source_by_id
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
        1: "pixiv-data",
        3: "twitter-data",
    }
    return class_map[form.site_id.data]


# #### Iterator functions

def site_metric_iterator(illust):
    site_data_json = illust.site_data.to_json()
    for key, val in site_data_json.items():
        if key in ['retweets', 'replies', 'quotes', 'bookmarks', 'views']:
            yield key, val


def site_date_iterator(illust):
    site_data_json = illust.site_data.to_json()
    for key, val in site_data_json.items():
        if key in ['site_updated', 'site_uploaded']:
            yield SITE_DATA_LABELS[key], val


# #### URL functions

def site_short_link(illust):
    site_key = get_site_key(illust.site_id)
    return "%s #%d" % (site_key.lower(), illust.site_illust_id)


def site_illust_url(illust):
    site_key = get_site_key(illust.site_id)
    source = SOURCEDICT[site_key]
    return source.get_illust_url(illust.site_illust_id)


def danbooru_batch_url(illust):
    source = get_source_by_id(illust.site_id)
    post_url = source.get_post_url(illust)
    query_string = urllib.parse.urlencode({'url': post_url})
    return DANBOORU_HOSTNAME + '/uploads/batch?' + query_string


# #### Link functions

# ###### INDEX

def post_search_link(illust):
    return general_link('»', search_url_for('post.index_html', illust_urls={'illust_id': illust.id}))


def illust_url_search_link(illust):
    return general_link("«search»", search_url_for('illust_url.index_html', illust_id=illust.id))


# ###### SHOW

def danbooru_upload_link(illust):
    return external_link("Danbooru", danbooru_batch_url(illust))


def update_from_source_link(illust):
    url = url_for('illust.query_update_html', id=illust.id)
    addons = {'onclick': "return Prebooru.linkPost(this)"}
    return general_link("Update from source", url, **addons)


def add_media_url_link(illust):
    return general_link("Add media url", url_for('illust_url.new_html', illust_id=illust.id))


def add_notation_link(illust):
    return general_link("Add notation", url_for('notation.new_html', illust_id=illust.id))


def add_pool_link(illust):
    url = url_for('pool_element.create_html')
    addons = {'onclick': "return Prebooru.createPool(this, 'illust')", 'data-illust-id': illust.id}
    return general_link("Add to pool", url, **addons)


def delete_commentary_link(illust, commentary):
    url = url_for('illust.delete_commentary_html', id=illust.id, description_id=commentary.id)
    return general_link("remove", url, method="DELETE", **{'class': 'warning-link'})


# ###### GENERAL

def site_illust_link(illust):
    return external_link(site_short_link(illust), site_illust_url(illust))


def alt_site_illust_link(illust):
    site_key = get_site_key(illust.site_id)
    source = SOURCEDICT[site_key]
    post_url = source.get_post_url(illust)
    return external_link('»', post_url) if post_url != source.get_illust_url(illust.site_illust_id) else ""
