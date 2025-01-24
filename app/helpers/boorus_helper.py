# APP/HELPERS/BOORUS_HELPER.PY

# ## PYTHON IMPORTS
import urllib.parse

# ## EXTERNAL IMPORTS
from flask import url_for

# ## PACKAGE IMPORTS
from config import DANBOORU_HOSTNAME

# ## LOCAL IMPORTS
from ..logical.utility import search_url_for
from .base_helper import general_link, external_link


# ## FUNCTIONS

# #### URL functions

def illust_search(booru):
    return search_url_for('illust.index_html', artist={'boorus': {'id': booru.id}})


def post_search(booru):
    return search_url_for('post.index_html', illust_urls={'illust': {'artist': {'boorus': {'id': booru.id}}}})


def danbooru_page_url(booru):
    return DANBOORU_HOSTNAME + '/artists/' + str(booru.danbooru_id)


def danbooru_post_search(booru):
    return DANBOORU_HOSTNAME + '/posts?' + urllib.parse.urlencode({'tags': booru.name_value + ' status:any'})


# #### Link functions

# ###### SHOW

def query_update_link(booru):
    return general_link("Update from source", url_for('booru.query_update_html', id=booru.id), method="POST")


def check_artists_link(booru):
    return general_link("Check for artists", url_for('booru.check_artists_html', id=booru.id), method="POST")


def add_artist_link(booru):
    addons = {'onclick': "return Boorus.addArtist(this)"}
    return general_link("Add artist", url_for('booru.add_artist_html', id=booru.id), **addons)


def remove_artist_link(booru, artist):
    url = url_for('booru.remove_artist_html', id=booru.id, artist_id=artist.id)
    return general_link('remove', url, method="DELETE", **{'class': 'warning-link'})


def add_notation_link(booru):
    return general_link("Add notation", url_for('notation.new_html', booru_id=booru.id, redirect='true'))


def delete_name_link(booru, name):
    return general_link("remove", url_for('booru.delete_name_html', id=booru.id, label_id=name.id),
                        method="DELETE", **{'class': 'warning-link'})


def swap_name_link(booru, name):
    url = url_for('booru.swap_name_html', id=booru.id, label_id=name.id)
    return general_link("swap", url, method="PUT", **{'class': 'notice-link'})


def names_link(booru):
    return general_link("Names (%d)" % booru.names_count, url_for('booru.names_html', id=booru.id))


# ###### GENERAL

def post_search_link(booru):
    return general_link('»', post_search(booru))


def site_booru_link(booru):
    return external_link(booru.name_value, danbooru_page_url(booru))


def site_search_link(booru):
    return external_link('»', danbooru_post_search(booru))
