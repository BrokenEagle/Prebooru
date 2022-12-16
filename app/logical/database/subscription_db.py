# APP/LOGICAL/DATABASE/SUBSCRIPTION_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import func

# ## PACKAGE IMPORTS
from utility.time import get_current_time, hours_from_now, add_days, days_ago

# ## LOCAL IMPORTS
from ... import SESSION
from ...enum_imports import subscription_status
from ...models import Subscription, SubscriptionElement, IllustUrl, Illust
from .base_db import update_column_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['artist_id', 'interval', 'expiration', 'last_id', 'requery', 'checked']

CREATE_ALLOWED_ATTRIBUTES = ['artist_id', 'interval', 'expiration']
UPDATE_ALLOWED_ATTRIBUTES = ['interval', 'expiration']

MAXIMUM_PROCESS_SUBSCRIPTIONS = 10

AVERAGE_INTERVAL_CLAUSE = (Subscription.checked - func.min(Illust.site_created)) / func.count(Illust.id)

# ## FUNCTIONS

# #### Route DB functions

# ###### Create

def create_subscription_from_parameters(createparams):
    if 'status' in createparams:
        createparams['status_id'] = Subscription.status_enum.by_name(createparams['status']).id
    current_time = get_current_time()
    subscription = Subscription(status_id=subscription_status.idle.id, created=current_time, updated=current_time)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(subscription, update_columns, createparams)
    print("[%s]: created" % subscription.shortlink)
    return subscription


# ###### Update

def update_subscription_from_parameters(subscription, updateparams):
    if 'status' in updateparams:
        updateparams['status_id'] = Subscription.status_enum.by_name(updateparams['status']).id
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


def update_subscription_status(subscription, value):
    subscription.status_id = subscription_status.by_name(value).id
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
    status_filter = Subscription.status_filter('name', 'not_in', ['manual', 'automatic'])
    query = Subscription.query.enum_join(Subscription.status_enum)\
                              .filter(Subscription.requery < get_current_time(),
                                      Subscription.last_id.is_not(None),
                                      status_filter)
    if not unlimited:
        query = query.limit(MAXIMUM_PROCESS_SUBSCRIPTIONS)
    return query.all()


def get_busy_subscriptions():
    return Subscription.query.enum_join(Subscription.status_enum)\
                             .filter(Subscription.status_filter('name', 'in_', ['manual', 'automatic']))\
                             .all()


def check_processing_subscriptions():
    return Subscription.query.enum_join(Subscription.status_enum)\
                             .filter(Subscription.status_filter('name', '__eq__', 'manual'))\
                             .get_count() > 0


def get_subscription_by_ids(subscription_ids):
    return Subscription.query.filter(Subscription.id.in_(subscription_ids)).all()


# #### Misc

def add_subscription_error(subscription, error):
    subscription.errors.append(error)
    subscription.status_id = subscription_status.error.id
    subscription.checked = get_current_time()
    subscription.requery = None
    SESSION.commit()


def delay_subscription_elements(subscription, delay_days):
    current_time = get_current_time()
    for element in subscription.undecided_elements:
        if delay_days == 0:
            element.expires = None
        else:
            element.expires = add_days(max(element.expires or current_time, current_time), delay_days)
    SESSION.commit()


def get_average_interval_for_subscriptions(subscriptions, days):
    keep_filter = SubscriptionElement.keep_filter('name', '__eq__', 'yes')
    return SubscriptionElement.query.enum_join(SubscriptionElement.keep_enum)\
                              .join(Subscription).join(IllustUrl).join(Illust)\
                              .with_entities(SubscriptionElement.subscription_id, AVERAGE_INTERVAL_CLAUSE)\
                              .filter(SubscriptionElement.subscription_id.in_([s.id for s in subscriptions]),
                                      Illust.site_created > days_ago(days),
                                      keep_filter,
                                      )\
                              .group_by(SubscriptionElement.subscription_id)\
                              .having(func.count(Illust.id) > 0).all()
