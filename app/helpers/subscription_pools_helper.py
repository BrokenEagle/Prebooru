# APP/HELPERS/ILLUSTS_HELPERS.PY

# ## EXTERNAL IMPORTS
from flask import url_for, request, Markup

# ## PACKAGE IMPORTS
from utility.data import readable_bytes

# ## LOCAL IMPORTS
from ..logical.utility import search_url_for
from .posts_helper import post_preview_link
from .base_helper import general_link, url_for_with_params, val_or_none


# ## GLOBAL VARIABLES

# ## FUNCTIONS

# #### Pools

# ###### URL functions

def post_search(subscription_pool):
    return search_url_for('post.index_html', type='subscription_post',
                          illust_urls={'illust': {'artist': {'subscription_pool': {'id': subscription_pool.id}}}})


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


def delay_subscription_link(subscription_pool):
    url = url_for('subscription_pool.delay_html', id=subscription_pool.id)
    addons = {'onclick': 'return SubscriptionPools.delaySubscriptionElements(this)'}
    return general_link("Delay expiration", url, **addons)


def get_last_job_status_link(subscription_pool):
    job_id = "process_subscription-%d" % subscription_pool.id
    url = url_for('subscription_pool.show_html', id=subscription_pool.id, job=job_id)
    return general_link("Get last job status", url)


def pool_status_link(subscription_pool):
    if subscription_pool.status == 'idle':
        return 'idle'
    url = url_for('subscription_pool.reset_html', id=subscription_pool.id)
    return general_link(subscription_pool.status, url, method='PUT')


# ###### Other functions

def average_interval(subscription_pool):
    if subscription_pool.element_count == 0:
        return Markup('<em>N/A</em>')
    return val_or_none(subscription_pool.average_keep_interval)


def storage_bytes(subscription_pool, type=None):
    switcher = {
        None: 'total_bytes',
        'main': 'main_bytes',
        'alternate': 'alternate_bytes',
    }
    size = getattr(subscription_pool, switcher[type])
    return readable_bytes(size) if size > 0 else Markup('<em>N/A</em>')


# #### Elements

def keep_element_val(subscription_element):
    return subscription_element.keep if subscription_element.keep is not None else Markup("<em>Not yet chosen</em>")


# ###### Link functions

def element_preview_link(element, lazyload):
    if element.post_match is not None:
        return post_preview_link(element.post_match, lazyload)
    elif element.archive_match is not None:
        preview_url = element.archive_match.preview_url
        width = element.archive_match.data['body']['width']
        height = element.archive_match.data['body']['height']
        file_ext = element.archive_match.data['body']['file_ext']
        size = element.archive_match.data['body']['size']
        title = f"( {width} x {height} ) : {file_ext.upper()} @ {readable_bytes(size)}"
    else:
        preview_url = element.illust_url.preview_url
        title = f"( {element.illust_url.width} x  {element.illust_url.height} )"
    addons = {
        'data-src': preview_url,
        'onerror': 'Prebooru.onImageError(this)',
        'title': title,
    }
    if not lazyload:
        addons['src'] = preview_url
    attrs = ['%s="%s"' % (k, v) for (k, v) in addons.items()]
    return Markup('<img %s>' % ' '.join(attrs))


def keep_element_link(subscription_element, value, format, has_preview):
    preview = 'yes' if has_preview else 'no'
    url = url_for('subscription_pool_element.keep_' + format, id=subscription_element.id, keep=value, preview=preview)
    addons = {'class': value + '-link keep-link'}
    if format == 'html':
        addons['onclick'] = "return Prebooru.linkPost(this)"
    elif format == 'json':
        addons['onclick'] = "return SubscriptionPools.keepElement(this)" if has_preview\
                            else "return Prebooru.keepElement(this)"
        addons['ondragstart'] = "return SubscriptionPools.dragKeepClick(this)"
    return general_link(value, url, **addons)


def element_type_link(element_type):
    active_type = request.args.get('type') or 'undecided'
    classes = ['element-type'] + [element_type + '-type'] + (['type-active'] if active_type == element_type else [])
    url = url_for_with_params('subscription_pool_element.index_html', type=element_type, page=None)
    return general_link(element_type.title(), url, **{'class': ' '.join(classes)})


def redownload_element_link(text, element):
    url = url_for('subscription_pool_element.redownload_json', id=element.id)
    return general_link(text, url, onclick="return SubscriptionPools.redownload(this)")
