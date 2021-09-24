# APP/MODELS/TAGS_HELPER.PY

# ## PYTHON IMPORTS
from flask import Markup

# ## LOCAL IMPORTS
from ..logical.sources import SOURCES
from .base_helper import search_url_for, general_link, external_link


# ## FUNCTIONS

# #### URL functions

def illust_search(tag):
    return search_url_for('illust.index_html', tags={'id': tag.id})


def post_search(tag):
    return search_url_for('post.index_html', illust_urls={'illust': {'tags': {'id': tag.id}}})


# #### Link functions

def post_search_link(tag):
    return general_link('&raquo;', post_search(tag))


def tag_search_links(tag):
    return Markup(' | ').join([external_link(source.NAME.title(), source.tag_search_url(tag)) for source in SOURCES if source.HAS_TAG_SEARCH])

