# APP/HELPERS/SUBSCRIPTIONS_HELPERS.PY

# ## EXTERNAL IMPORTS
from flask import url_for, request, Markup

# ## PACKAGE IMPORTS
from config import MAXIMUM_PROCESS_SUBSCRIPTIONS, DOWNLOAD_POSTS_PER_PAGE, DOWNLOAD_POSTS_PAGE_LIMIT,\
    UNLINK_ELEMENTS_PER_PAGE, DELETE_ELEMENTS_PER_PAGE, ARCHIVE_ELEMENTS_PER_PAGE, EXPIRE_ELEMENTS_PAGE_LIMIT
from utility.data import readable_bytes

# ## LOCAL IMPORTS
from ..logical.utility import search_url_for
from ..logical.database.subscription_db import get_average_interval_for_subscriptions, get_available_subscriptions_query
from ..logical.database.subscription_element_db import expired_subscription_elements,\
    pending_subscription_downloads_query
from ..logical.records.subscription_rec import subscription_slots_needed_per_hour
from ..logical.tasks import JOB_CONFIG
from .archives_helper import archive_preview_link
from .posts_helper import post_preview_link
from .base_helper import general_link, url_for_with_params


# ## GLOBAL VARIABLES

ELEMENTS_PER_BATCH = {
    'unlink': UNLINK_ELEMENTS_PER_PAGE * EXPIRE_ELEMENTS_PAGE_LIMIT,
    'delete': DELETE_ELEMENTS_PER_PAGE * EXPIRE_ELEMENTS_PAGE_LIMIT,
    'archive': ARCHIVE_ELEMENTS_PER_PAGE * EXPIRE_ELEMENTS_PAGE_LIMIT,
}


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


def recheck_subscription_link(subscription):
    url = url_for('subscription.recheck_html', id=subscription.id)
    return general_link("Recheck subscription", url, method="POST")


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


def retire_link(subscription):
    url = url_for('subscription.retire_html', id=subscription.id)
    return general_link("Retire subscription", url, method='PUT')


def element_keep_link(subscription, keep):
    search_args = {'subscription_id': subscription.id}
    if keep is not None:
        search_args['keep'] = keep
    else:
        search_args['keep_exists'] = 'false'
    url = search_url_for('subscription_element.index_html', base_args={'type': 'all'}, **search_args)
    return general_link('»', url)


def element_status_link(subscription, status):
    search_args = {'subscription_id': subscription.id, 'status': status}
    url = search_url_for('subscription_element.index_html', base_args={'type': 'all'}, **search_args)
    return general_link('»', url)


# ###### Iterator functions

def subscriptions_iterator():
    hours = _hours_from_config(JOB_CONFIG['check_pending_subscriptions']['config'])
    output = {
        "Slots Per Interval": MAXIMUM_PROCESS_SUBSCRIPTIONS,
        "Processed Every": "%0.1f hours" % hours,
        "Slots Per Hour": "%0.1f" % (MAXIMUM_PROCESS_SUBSCRIPTIONS / hours),
        "Pending": get_available_subscriptions_query().get_count(),
    }
    for key, value in output.items():
        yield key, value


def slots_per_hour_iterator():
    needed = subscription_slots_needed_per_hour()
    for i in range(4, 28, 4):
        yield "%0.2f" % ((24 / i) * needed)


def download_iterator():
    hours = hours = _hours_from_config(JOB_CONFIG['check_pending_downloads']['config'])
    per_interval = DOWNLOAD_POSTS_PER_PAGE * DOWNLOAD_POSTS_PAGE_LIMIT
    output = {
        "Downloads Per interval": per_interval,
        "Processed Every": "%0.1f hours" % hours,
        "Downloads Per Hour": "%0.1f" % (per_interval / hours),
        "Pending": pending_subscription_downloads_query().get_count(),
    }
    for key, value in output.items():
        yield key, value


def expires_iterator():
    for key in ['unlink', 'delete', 'archive']:
        hours = _hours_from_config(JOB_CONFIG[f'{key}_expired_subscription_elements']['config'])
        per_batch = ELEMENTS_PER_BATCH[key]
        pending = expired_subscription_elements(key).get_count()
        completion = (pending / per_batch) * hours
        yield key, hours, per_batch, pending, completion


# ###### Other functions

def average_interval_lookup(subscription, average_intervals):
    interval = next((interval for interval in average_intervals if interval[0] == subscription.id), None)
    if interval is None:
        return Markup('<em>N/A</em>')
    return "%0.2f" % (interval[1] / 3600)


def average_interval(subscription):
    interval = get_average_interval_for_subscriptions([subscription], 365)
    if len(interval) == 0:
        return Markup('<em>N/A</em>')
    return "%0.2f" % (interval[0][1] / 3600)


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


# #### Private

def _hours_from_config(config):
    if 'hours' in config:
        return config['hours']
    if 'minutes' in config:
        return config['minutes'] / 60
    if 'days' in config:
        return config['days'] * 24
