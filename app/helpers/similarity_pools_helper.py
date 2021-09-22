# APP\HELPERS\SIMILARITY_HELPER.PY

# ## PYTHON IMPORTS
from flask import url_for

# ## LOCAL IMPORTS
from .base_helper import GeneralLink


# ## FUNCTIONS

def SiblingPoolLink(similarity_element):
    return GeneralLink(similarity_element.post.shortlink, similarity_element.sibling.pool.show_url)
