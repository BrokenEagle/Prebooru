# APP/HELPERS/BOORUS_HELPER.PY

# ##PYTHON IMPORTS
import urllib.parse
from flask import url_for

# ##LOCAL IMPORTS
from ..config import DANBOORU_HOSTNAME
from .base_helper import search_url_for, general_link, external_link


# ## FUNCTIONS

# #### URL functions

def illust_search(booru):
    return search_url_for('illust.index_html', artist={'boorus': {'id': booru.id}})


def post_search(booru):
    return search_url_for('post.index_html', illust_urls={'illust': {'artist': {'boorus': {'id': booru.id}}}})


def danbooru_page_url(booru):
    return DANBOORU_HOSTNAME + '/artists/' + str(booru.danbooru_id)


def danbooru_post_search(booru):
    return DANBOORU_HOSTNAME + '/posts?' + urllib.parse.urlencode({'tags': booru.current_name + ' status:any'})


# #### Link functions

# ###### SHOW

def query_update_link(booru):
    return general_link("Update from source", url_for('booru.query_update_html', id=booru.id), method="POST")


def check_artists_link(booru):
    return general_link("Check for artists", url_for('booru.check_artists_html', id=booru.id), method="POST")


# ###### GENERAL

def post_search_link(booru):
    return general_link('&raquo;', post_search(booru))


def site_booru_link(booru):
    return external_link(booru.current_name, danbooru_page_url(booru))


def site_search_link(booru):
    return external_link('&raquo;', danbooru_post_search(booru))
