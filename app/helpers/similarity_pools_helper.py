# APP\HELPERS\SIMILARITY_HELPER.PY

# ## PYTHON IMPORTS
from flask import url_for

# ## LOCAL IMPORTS
from .base_helper import GeneralLink


# ## FUNCTIONS

def SiblingPoolLink(element, post):
    return GeneralLink(post.shortlink, url_for('similarity_pool.show_html', id=element.sibling.pool_id))
