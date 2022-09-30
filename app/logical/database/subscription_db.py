# APP/LOGICAL/DATABASE/SUBSCRIPTION_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time, hours_from_now, add_days

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Subscription
from .base_db import update_column_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['artist_id', 'interval', 'expiration', 'last_id', 'requery', 'checked', 'active']

CREATE_ALLOWED_ATTRIBUTES = ['artist_id', 'interval', 'expiration', 'active']
UPDATE_ALLOWED_ATTRIBUTES = ['interval', 'expiration', 'active']

MAXIMUM_PROCESS_SUBSCRIPTIONS = 10


# ## FUNCTIONS

# #### Route DB functions

# ###### Create

def create_subscription_from_parameters(createparams):
    current_time = get_current_time()
    subscription = Subscription(status='idle', created=current_time, updated=current_time)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(subscription, update_columns, createparams)
    print("[%s]: created" % subscription.shortlink)
    return subscription


# ###### Update

def update_subscription_from_parameters(subscription, updateparams):
    update_results = []
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(update_column_attributes(subscription, update_columns, updateparams))
    if subscription.requery is not None and subscription.requery > hours_from_now(subscription.interval):
        update_subscription_requery(subscription, hours_from_now(subscription.interval))
    if any(update_results):
        print("[%s]: updated" % subscription.shortlink)
        subscription.updated = get_current_time()
        SESSION.commit()


def update_subscription_status(subscription, status):
    subscription.status = status
    SESSION.commit()


def update_subscription_active(subscription, active):
    subscription.active = active
    SESSION.commit()


def update_subscription_requery(subscription, timeval):
    subscription.requery = timeval
    SESSION.commit()


def update_subscription_last_info(subscription, last_id):
    subscription.last_id = last_id
    subscription.checked = get_current_time()
    SESSION.commit()


# ###### Delete

def delete_subscription(subscription):
    SESSION.delete(subscription)
    SESSION.commit()


# #### Query

def get_available_subscription(unlimited):
    # Return only subscriptions which have already been processed manually (requery is not None)
    query = Subscription.query.filter(Subscription.requery < get_current_time(),
                                      Subscription.active.is_(True),
                                      Subscription.status.not_in(['manual', 'automatic']))
    if not unlimited:
        query = query.limit(MAXIMUM_PROCESS_SUBSCRIPTIONS)
    return query.all()


def get_busy_subscriptions():
    return Subscription.query.filter(Subscription.status.in_(['manual', 'automatic'])).all()


def check_processing_subscriptions():
    return Subscription.query.filter_by(status='manual').get_count() > 0


def get_subscription_by_ids(subscription_ids):
    return Subscription.query.filter(Subscription.id.in_(subscription_ids)).all()


# #### Misc

def add_subscription_error(subscription, error):
    subscription.errors.append(error)
    subscription.status = 'error'
    subscription.checked = get_current_time()
    subscription.requery = None
    subscription.active = False
    SESSION.commit()


def delay_subscription_elements(subscription, delay_days):
    current_time = get_current_time()
    for element in subscription.active_elements:
        if element.keep and element.keep.name == 'maybe':
            continue
        if delay_days == 0:
            element.expires = None
        else:
            element.expires = add_days(max(element.expires or current_time, current_time), delay_days)
    SESSION.commit()
