# APP\HELPERS\SIMILARITY_POOLS_HELPER.PY

# ## LOCAL IMPORTS
from .base_helper import general_link


# ## FUNCTIONS

# #### Link functions

def pool_count_link(similarity_pool):
    return general_link(similarity_pool.element_count, similarity_pool.show_url)


def sibling_pool_link(similarity_element):
    return general_link(similarity_element.post_shortlink, similarity_element.sibling.pool_show_url)


def delete_element_link(element):
    return general_link("remove", element.delete_url, method="DELETE", **{'class': 'warning-link'})
