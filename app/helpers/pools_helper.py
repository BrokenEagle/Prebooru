# APP/HELPERS/POOLS_HELPER.PY

# ## EXTERNAL IMPORTS
from flask import url_for

# ## LOCAL IMPORTS
from .base_helper import general_link


# ## FUNCTIONS

# #### Format functions

def media_header(item):
    if item.model_name == 'illust':
        return item.type.title() + ':'
    if item.model_name == 'post':
        return ('Video' if item.file_ext in ['mp4'] else 'Image') + ':'
    return ""


# #### Link functions

def last_page_link(pool):
    return general_link('»', url_for('pool.show_last_html', id=pool.id))


def prev_navigation(pool_element):
    return _pool_navigation('«', 'pool_element.previous_html', pool_element)


def next_navigation(pool_element):
    return _pool_navigation('»', 'pool_element.next_html', pool_element)


def page_navigation(pool_element):
    text = "%d/%d" % (pool_element.position1, pool_element.pool.element_count)
    return general_link(text, pool_element.page_url)


def remove_pool_link(pool_element):
    return general_link("remove", pool_element.delete_url, method="DELETE", **{'class': 'warning-link'})


# #### Private functions

def _pool_navigation(text, endpoint, pool_element):
    return general_link(text, url_for(endpoint, id=pool_element.id)) if pool_element.pool.series else ""
