# APP/HELPERS/BOORUS_HELPER.PY

# ## PYTHON IMPORTS
import urllib.parse

# ## EXTERNAL IMPORTS
from flask import url_for

# ## PACKAGE IMPORTS
from config import DANBOORU_HOSTNAME

# ## LOCAL IMPORTS
from ..logical.utility import search_url_for
from .base_helper import general_link, external_link, post_link, put_link, delete_link


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
    return post_link("Update from source", url_for('booru.query_update_html', id=booru.id))


def check_artists_link(booru):
    return post_link("query Danbooru", url_for('booru.check_artists_html', id=booru.id))


def add_artist_link(booru):
    addons = {'prompt': "Enter artist ID to add:", 'prompt-arg': 'artist_id'}
    return general_link("+", url_for('booru.add_artist_html', id=booru.id), **addons)


def remove_artist_link(booru, artist):
    return delete_link('remove', url_for('booru.remove_artist_html', id=booru.id, artist_id=artist.id))


def delete_name_link(booru, name):
    return delete_link("remove", url_for('booru.delete_name_html', id=booru.id, label_id=name.id))


def swap_name_link(booru, name):
    return put_link("swap", url_for('booru.swap_name_html', id=booru.id, label_id=name.id))


def names_link(booru):
    return general_link("Names (%d)" % booru.names_count, url_for('booru.names_html', id=booru.id))


# ###### GENERAL

def post_search_link(booru):
    return general_link('»', post_search(booru))


def site_booru_link(booru):
    return external_link(booru.name_value, danbooru_page_url(booru))


def site_search_link(booru):
    return external_link('»', danbooru_post_search(booru))
