# APP/MODELS/TAGS_HELPER.PY

# ## EXTERNAL IMPORTS
from flask import Markup, url_for

# ## LOCAL IMPORTS
from ..logical.utility import search_url_for
from ..logical.sources import SOURCES
from .base_helper import general_link, external_link


# ## FUNCTIONS

# #### URL functions

def illust_search(tag, item_type):
    if item_type == 'illust':
        return search_url_for('illust.index_html', tags={'id': tag.id})
    elif item_type == 'post':
        return search_url_for('illust.index_html', illust_urls={'posts': {'tags': {'id': tag.id}}})


def post_search(tag, item_type):
    if item_type == 'illust':
        return search_url_for('post.index_html', illust_urls={'illust': {'tags': {'id': tag.id}}})
    elif item_type == 'post':
        return search_url_for('post.index_html', tags={'id': tag.id})


# #### Link functions

def post_search_link(tag, item_type):
    return general_link('»', post_search(tag, item_type))


def tag_search_links(tag):
    links = [external_link(source.SITE.name.title(), source.tag_search_url(tag))
             for source in SOURCES if source.HAS_TAG_SEARCH]
    return Markup(' | ').join(links)


def remove_tag_link(tag, item_type, item_id):
    url = url_for('tag.remove_item_show_json', id=tag.id, preview='true')
    addons = {
        'onclick': f"return Prebooru.removeTag(this, '{item_type}')",
        f'data-{item_type}-id': item_id,
        'class': 'warning-link'
    }
    return general_link("remove", url, **addons)
