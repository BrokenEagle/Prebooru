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

HTTP_RG = re.compile(r'(\b(?:http|https)(?::\/{2}[\w]+)(?:[\/|\.]?)(?:[^\s<>\uff08\uff09\u3011\u3000"\[\]]*))', re.IGNORECASE | re.ASCII)
SHORTLINK_RG = re.compile(r'\b(booru|artist|illust|post|upload|pool|notation) #(\d+)\b', re.IGNORECASE)

APPEND_ATTRS = ['_pool', 'artist', 'illust', 'post']
APPEND_KEY_DICT = {
    '_pool': 'pool',
    'artist': 'artist',
    'illust': 'illust',
    'post': 'post',
}


# ## FUNCTIONS

# #### Helper functions

def is_general_form(form):  # Unused
    return (form.pool_id.data is None) and (form.artist_id.data is None) and (form.illust_id.data is None) and (form.post_id.data is None)


# #### General functions

def convert_to_html(notation):
    links = HTTP_RG.findall(notation.body)
    output_html = html.escape(notation.body)
    for link in links:
        escaped_link = re.escape(html.escape(link))
        link_match = re.search(escaped_link, output_html)
        if link_match is None:
            continue
        html_link = '<a href="%s">%s</a>' % (link, link)
        output_html = output_html[:link_match.start()] + html_link + output_html[link_match.end():]
    output_html = re.sub(r'\r?\n', '<br>', output_html)
    output_html = convert_short_links(output_html)
    return Markup(output_html)


def convert_short_links(notation_text):
    position = 0
    while True:
        match = SHORTLINK_RG.search(notation_text, pos=position)
        if not match:
            return notation_text
        link_url = url_for(match.group(1) + '.show_html', id=int(match.group(2)))
        link = str(general_link(match.group(0), link_url))
        notation_text = notation_text[:match.start()] + link + notation_text[match.end():]
        position = match.start() + len(link)


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
