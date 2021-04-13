# APP/MODELS/TAGS_HELPER.PY

# ## PYTHON IMPORTS
from flask import Markup

# ## LOCAL IMPORTS
from ..sources import SOURCES
from .base_helper import SearchUrlFor, ExternalLink


# ## FUNCTIONS

def IllustSearch(tag):
    return SearchUrlFor('illust.index_html', tags={'id': tag.id})


def PostSearch(tag):
    return SearchUrlFor('post.index_html', illust_urls={'illust': {'tags': {'id': tag.id}}})


def TagSearchLinks(tag):
    return Markup(' | ').join([ExternalLink(source.NAME.title(), source.TagSearchUrl(tag)) for source in SOURCES if source.HAS_TAG_SEARCH])
