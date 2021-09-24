# APP/HELPERS/NOTATIONS_HELPERS.PY

# ##PYTHON IMPORTS
import re
import html
from flask import Markup, url_for

# ##LOCAL IMPORTS
from .base_helper import convert_str_to_html, general_link
from . import artists_helper as ARTIST
from . import illusts_helper as ILLUST


# ##GLOBAL VARIABLES

APPEND_ATTRS = ['_pool', 'artist', 'illust', 'post']
APPEND_KEY_DICT = {
    '_pool': 'pool',
    'artist': 'artist',
    'illust': 'illust',
    'post': 'post',
}


# ## FUNCTIONS

# #### Route functions

# ###### INDEX

def body_excerpt(notation):
    lines = re.split(r'\r?\n', notation.body)
    return convert_str_to_html(lines[0][:50] + ('...' if len(lines[0]) > 50 else ''))


# ###### SHOW

def item_link(item):
    return general_link(item_link_title(item), item.show_url)


def item_link_title(item):
    if item.__table__.name == 'pool':
        return item.name
    if item.__table__.name == 'artist':
        return ARTIST.short_link(item)
    if item.__table__.name == 'illust':
        return ILLUST.short_link(item)
    return item.header


def has_append_item(notation):
    return any((getattr(notation, attr) is not None) for attr in ['_pool', 'artist', 'illust', 'post'])


def append_key(notation):
    return next((key, getattr(notation, attr)) for (attr, key) in APPEND_KEY_DICT.items() if (getattr(notation, attr) is not None))
