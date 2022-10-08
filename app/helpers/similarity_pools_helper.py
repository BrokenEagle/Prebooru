# APP/HELPERS/SIMILARITY_POOLS_HELPER.PY

# ## EXTERNAL IMPORTS
from flask import url_for

# ## LOCAL IMPORTS
from ..logical.utility import search_url_for
from .base_helper import general_link


# ## FUNCTIONS

# #### Link functions

def pool_count_link(post):
    url = search_url_for('similarity_pool_element.index_html', pool_id=post.id)
    return general_link(post.similar_post_count, url)


def delete_element_link(element, is_json):
    if is_json:
        url = url_for('similarity_pool_element.delete_json', id=element.id)
        addons = {
            'class': 'warning-link',
            'onclick': "return SimilarityPools.deleteElement(this)",
        }
        return general_link("remove", url, **addons)
    else:
        return general_link("remove", element.delete_url, method="DELETE", **{'class': 'warning-link'})


def pool_show_link(element):
    url = search_url_for('similarity_pool_element.index_html', pool_id=element.pool_id)
    return general_link(element.pool.shortlink, url)
