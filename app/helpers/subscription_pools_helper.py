# APP/HELPERS/ILLUSTS_HELPERS.PY

# ## EXTERNAL IMPORTS
from flask import url_for, request, Markup

# ## LOCAL IMPORTS
from ..logical.utility import search_url_for
from .base_helper import general_link, url_for_with_params, val_or_none


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


def get_last_job_status_link(subscription_pool):
    job_id = "process_subscription-%d" % subscription_pool.id
    url = url_for('subscription_pool.show_html', id=subscription_pool.id, job=job_id)
    return general_link("Get last job status", url)


def pool_status_link(subscription_pool):
    return 'idle' if subscription_pool.status == 'idle'\
                  else general_link(subscription_pool.status,
                                    url_for('subscription_pool.reset_html', id=subscription_pool.id),
                                    method='PUT')


# ###### Other functions

def average_interval(subscription_pool):
    if subscription_pool.element_count == 0:
        return Markup('<em>N/A</em>')
    return val_or_none(subscription_pool.average_keep_interval)


# #### Elements

def keep_element_val(subscription_element):
    return subscription_element.keep if subscription_element.keep is not None else Markup("<em>Not yet chosen</em>")


# ###### Link functions

def keep_element_link(subscription_element, value, format, has_preview):
    preview = 'yes' if has_preview else 'no'
    url = url_for('subscription_pool_element.keep_' + format, id=subscription_element.id, keep=value, preview=preview)
    addons = {'class': value + '-link keep-link'}
    if format == 'html':
        addons['onclick'] = "return Prebooru.linkPost(this)"
    elif format == 'json':
        addons['onclick'] = "return SubscriptionPools.keepElement(this)" if has_preview else "return Prebooru.keepElement(this)"
    return general_link(value, url, **addons)


def element_type_link(element_type):
    active_type = request.args.get('type') or 'unsure'
    classes = ['element-type'] + [element_type + '-type'] + (['type-active'] if active_type == element_type else [])
    url = url_for_with_params('subscription_pool_element.index_html', type=element_type, page=None)
    return general_link(element_type.title(), url, **{'class': ' '.join(classes)})


def redownload_element_link(text, element):
    return general_link(text, url_for('subscription_pool_element.redownload_html', id=element.id), method='POST')
