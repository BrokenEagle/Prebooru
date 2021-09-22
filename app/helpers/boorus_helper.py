# APP/HELPERS/BOORUS_HELPER.PY

# ##PYTHON IMPORTS
import urllib.parse

# ##LOCAL IMPORTS
from ..config import DANBOORU_HOSTNAME
from .base_helper import search_url_for, external_link


# ## FUNCTIONS

def illust_search(booru):
    return search_url_for('illust.index_html', artist={'boorus': {'id': booru.id}})


def post_search(booru):
    return search_url_for('post.index_html', illust_urls={'illust': {'artist': {'boorus': {'id': booru.id}}}})


def danbooru_page_url(booru):
    return DANBOORU_HOSTNAME + '/artists/' + str(booru.danbooru_id)


def danbooru_post_search(booru):
    return DANBOORU_HOSTNAME + '/posts?' + urllib.parse.urlencode({'tags': booru.current_name + ' status:any'})


# #### Link functions

def site_booru_link(booru):
    return external_link(booru.current_name, danbooru_page_url(booru))


def site_search_link(booru):
    return external_link('&raquo;', danbooru_post_search(booru))
