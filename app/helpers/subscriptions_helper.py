# APP/HELPERS/SUBSCRIPTIONS_HELPERS.PY

# ## EXTERNAL IMPORTS
from flask import url_for, request, Markup

# ## PACKAGE IMPORTS
from utility.data import readable_bytes
from utility.time import humanized_timedelta

# ## LOCAL IMPORTS
from ..logical.utility import search_url_for
from .archives_helper import archive_preview_link
from .posts_helper import post_preview_link
from .base_helper import general_link, url_for_with_params, val_or_none


# ## GLOBAL VARIABLES

# ## FUNCTIONS

# #### Subscriptions

# ###### URL functions

def post_search(subscription):
    return search_url_for('post.index_html', type='subscription',
                          illust_urls={'illust': {'artist': {'subscription': {'id': subscription.id}}}})


def illust_search(subscription):
    return search_url_for('illust.index_html', urls={'subscription_element': {'subscription_id': subscription.id}})


def element_search(item):
    if item.model_name == 'subscription':
        subscription_id = item.id
    elif item.model_name == 'subscription_element':
        subscription_id = item.subscription_id
    else:
        raise Exception("Invalid item for element search.")
    return search_url_for('subscription_element.index_html', subscription_id=subscription_id)


# ###### Link functions

def element_search_link(subscription):
    return general_link('»', element_search(subscription))


def process_subscription_link(subscription):
    url = url_for('subscription.process_html', id=subscription.id)
    return general_link("Process subscription", url, method="POST")


def delay_subscription_link(subscription):
    url = url_for('subscription.delay_html', id=subscription.id)
    addons = {'onclick': 'return Subscriptions.delaySubscriptionElements(this)'}
    return general_link("Delay expiration", url, **addons)


def get_last_job_status_link(subscription):
    job_id = "process_subscription_manual-%d" % subscription.id
    url = url_for('subscription.show_html', id=subscription.id, job=job_id)
    return general_link("Get last job status", url)


def status_link(subscription):
    if subscription.status.name == 'idle':
        return 'idle'
    url = url_for('subscription.reset_html', id=subscription.id)
    return general_link(subscription.status.name, url, method='PUT')


# ###### Other functions

def average_interval(subscription):
    if subscription.element_count == 0:
        return Markup('<em>N/A</em>')
    humanized_average_interval = subscription.average_interval and humanized_timedelta(subscription.average_interval)
    return val_or_none(humanized_average_interval)


def storage_bytes(subscription, type=None):
    switcher = {
        None: 'total_bytes',
        'main': 'main_bytes',
        'alternate': 'alternate_bytes',
    }
    size = getattr(subscription, switcher[type])
    return readable_bytes(size) if size > 0 else Markup('<em>N/A</em>')


# #### Elements

def keep_element_val(subscription_element):
    if subscription_element.keep is not None:
        return subscription_element.keep.name
    else:
        return Markup("<em>Not yet chosen</em>")


# ###### Link functions

def element_preview_link(element, lazyload):
    if element.post_match is not None:
        return post_preview_link(element.post_match, lazyload)
    if element.archive_match is not None:
        return archive_preview_link(element.archive_match, lazyload)
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


def keep_element_link(subscription_element, value, has_preview):
    preview = 'yes' if has_preview else 'no'
    url = url_for('subscription_element.keep_json', id=subscription_element.id, keep=value, preview=preview)
    addons = {
        'class': value + '-link keep-link',
        'onclick': 'return Subscriptions.networkHandler(this)',
        'ondragstart': 'return Subscriptions.dragKeepClick(this)',
        'data-preview': str(has_preview).lower(),
    }
    return general_link(value, url, **addons)


def element_type_link(element_type):
    active_type = request.args.get('type') or 'undecided'
    classes = ['element-type'] + [element_type + '-type'] + (['type-active'] if active_type == element_type else [])
    url = url_for_with_params('subscription_element.index_html', type=element_type, page=None)
    return general_link(element_type.title(), url, **{'class': ' '.join(classes)})


def nopost_function_link(name, element):
    url = url_for(f'subscription_element.{name}_json', id=element.id)
    addons = {
        'onclick': 'return Subscriptions.networkHandler(this)',
    }
    return general_link(name, url, **addons)
