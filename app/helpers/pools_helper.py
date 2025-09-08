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
        return item.media_type.title() + ':'
    return ""


# #### Link functions

def last_page_link(pool):
    return general_link('»', url_for('pool.show_last_html', id=pool.id))


def prev_navigation(pool_element):
    return _pool_navigation('«&nbsp;', 'pool_element.previous_html', pool_element)


def next_navigation(pool_element):
    return _pool_navigation('&nbsp;»', 'pool_element.next_html', pool_element)


def page_navigation(pool_element):
    text = "%d/%d" % (pool_element.position1, pool_element.pool.element_count)
    return general_link(text, pool_element.page_url)


def add_pool_link(item):
    if item.model_name == 'post':
        data_key = 'data-post-id'
    elif item.model_name == 'illust':
        data_key = 'data-illust-id'
    else:
        raise Exception("Invalid model for pool adds.")
    url = url_for('pool_element.create_json', preview='true')
    addons = {
        'class': 'action-link',
        'onclick': f"return Pools.createElement(this, '{item.model_name}')",
        data_key: item.id,
    }
    return general_link("+", url, **addons)


def remove_pool_link(pool_element):
    url = url_for('pool_element.delete_json', id=pool_element.id, preview='true')
    addons = {
        'class': 'warning-link',
        'onclick': "return Pools.deleteElement(this)",
    }
    return general_link("remove", url, **addons)


# #### Private functions

def _pool_navigation(text, endpoint, pool_element):
    return general_link(text, url_for(endpoint, id=pool_element.id)) if pool_element.pool.series else ""
