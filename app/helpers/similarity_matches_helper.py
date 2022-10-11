# APP/HELPERS/SIMILARITY_MATCHES_HELPER.PY

# ## EXTERNAL IMPORTS
from flask import url_for

# ## LOCAL IMPORTS
from ..logical.utility import search_url_for
from .base_helper import general_link


# ## FUNCTIONS

# #### Link functions

def pool_count_link(post):
    url = search_url_for('similarity_match.index_html', post_id=post.id)
    return general_link(post.similar_post_count, url)


def pool_show_link(post):
    url = search_url_for('similarity_match.index_html', post_id=post.id)
    return general_link(f'{post.shortlink}', url)


def delete_element_link(element, is_json):
    if is_json:
        url = url_for('similarity_match.delete_json', forward_id=element.forward_id, reverse_id=element.reverse_id)
        addons = {
            'class': 'warning-link',
            'onclick': "return SimilarityMatches.deleteElement(this)",
        }
        return general_link("remove", url, **addons)
    else:
        url = url_for('similarity_match.delete_html', forward_id=element.forward_id, reverse_id=element.reverse_id)
        return general_link("remove", url, method="DELETE", **{'class': 'warning-link'})
