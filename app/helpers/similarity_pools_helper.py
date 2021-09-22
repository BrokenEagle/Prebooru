# APP\HELPERS\SIMILARITY_HELPER.PY

# ## PYTHON IMPORTS
from flask import url_for

# ## LOCAL IMPORTS
from .base_helper import general_link


# ## FUNCTIONS

def sibling_pool_link(similarity_element):
    return general_link(similarity_element.post.shortlink, similarity_element.sibling.pool.show_url)
