# APP/HELPERS/SIMILARITY_POOLS_HELPER.PY

# ## EXTERNAL IMPORTS
from flask import url_for

# ## LOCAL IMPORTS
from .base_helper import general_link


# ## FUNCTIONS

# #### Link functions

def pool_count_link(similarity_pool):
    return general_link(similarity_pool.element_count, similarity_pool.show_url)


def sibling_pool_link(similarity_element):
    return general_link(similarity_element.post_shortlink, similarity_element.sibling.pool_show_url)


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
    return general_link(element.pool.post.shortlink, element.pool.show_url)
