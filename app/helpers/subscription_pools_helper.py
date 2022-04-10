# APP/HELPERS/ILLUSTS_HELPERS.PY

# ## EXTERNAL IMPORTS
from flask import url_for

# ## LOCAL IMPORTS
from .base_helper import search_url_for, general_link


# ## GLOBAL VARIABLES

# ## FUNCTIONS

# #### Pools

# ###### URL functions

def post_search(subscription_pool):
    return search_url_for('post.index_html', base_args={'type': 'subscription'},
                          subscription_pool_element={'pool_id': subscription_pool.id})


def illust_search(subscription_pool):
    return search_url_for('illust.index_html', urls={'subscription_pool_element': {'pool_id': subscription_pool.id}})


def element_search(item):
    if item.model_name == 'subscription_pool':
        pool_id = item.id
    elif item.model_name == 'subscription_pool_element':
        pool_id = item.pool_id
    else:
        raise Exception("Invalid item for element search.")
    return search_url_for('subscription_pool_element.index_html', pool_id=pool_id)


# ###### Link functions

def element_search_link(subscription_pool):
    return general_link('&raquo;', element_search(subscription_pool))


def process_subscription_link(subscription_pool):
    url = url_for('subscription_pool.process_html', id=subscription_pool.id)
    return general_link("Process subscription", url, method="POST")
