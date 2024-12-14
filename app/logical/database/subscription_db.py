# APP/LOGICAL/DATABASE/SUBSCRIPTION_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import func

# ## PACKAGE IMPORTS
from utility.time import get_current_time, hours_from_now, add_days, days_ago

# ## LOCAL IMPORTS
from ...enum_imports import subscription_status
from ...models import Subscription, SubscriptionElement, IllustUrl, Illust
from .base_db import update_column_attributes, delete_record, save_record, commit_session


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['interval', 'expiration']
NULL_WRITABLE_ATTRIBUTES = ['artist_id']

DISTINCT_ILLUST_COUNT = func.count(Illust.id.distinct())
UNDECIDED_COUNT = func.count(SubscriptionElement.keep_filter('id', 'is_', None))
DISTINCT_ELEMENT_COUNT = func.count(SubscriptionElement.id.distinct())
COUNT_UNDECIDED_ELEMENTS = func.sum(func.iif(SubscriptionElement.keep_filter('id', 'is_', None), 1, 0)).label('count')


# ## FUNCTIONS

# #### Route DB functions

# ###### Create

def create_subscription_from_parameters(createparams):
    if 'status' in createparams:
        createparams['status_id'] = Subscription.status_enum.by_name(createparams['status']).id
    current_time = get_current_time()
    subscription = Subscription(status_id=subscription_status.idle.id, created=current_time, updated=current_time)
    update_column_attributes(subscription, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, createparams)
    save_record(subscription, 'created')
    return subscription


# ###### Update

def update_subscription_from_parameters(subscription, updateparams):
    if 'status' in updateparams:
        updateparams['status_id'] = Subscription.status_enum.by_name(updateparams['status']).id
    if subscription.requery is not None and subscription.requery > hours_from_now(subscription.interval):
        update_subscription_requery(subscription, hours_from_now(subscription.interval))
    if update_column_attributes(subscription, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, updateparams):
        subscription.updated = get_current_time()
        save_record(subscription, 'updated')


def update_subscription_status(subscription, value):
    subscription.status_id = subscription_status.by_name(value).id
    commit_session()


def update_subscriptions_status(subscriptions, value):
    for subscription in subscriptions:
        subscription.status_id = subscription_status.by_name(value).id
    commit_session()


def update_subscription_requery(subscription, timeval):
    subscription.requery = timeval
    commit_session()


def update_subscription_last_info(subscription):
    subscription.checked = get_current_time()
    subscription.last_id = subscription.artist.last_illust_id
    commit_session()


# ###### Delete

def delete_subscription(subscription):
    delete_record(subscription)
    commit_session()


# #### Query

def get_available_subscriptions_query():
    # Return only subscriptions which have already been processed manually (requery is not None)
    status_filter = Subscription.status_filter('name', '__eq__', 'idle')
    return Subscription.query.enum_join(Subscription.status_enum)\
                             .filter(Subscription.requery < get_current_time(), status_filter)\
                             .order_by(Subscription.requery.asc())


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


def ordered_subscriptions_by_pending_elements(limit):
    return SubscriptionElement.query.enum_join(SubscriptionElement.status_enum)\
                                    .with_entities(SubscriptionElement.subscription_id, DISTINCT_ELEMENT_COUNT)\
                                    .filter(SubscriptionElement.keep_filter('name', 'is_', None),
                                            SubscriptionElement.status_filter('name', '__eq__', 'active')
                                            )\
                                    .group_by(SubscriptionElement.subscription_id)\
                                    .having(DISTINCT_ELEMENT_COUNT > 0)\
                                    .order_by(DISTINCT_ELEMENT_COUNT.desc())\
                                    .limit(limit)\
                                    .all()


# #### Misc

def add_subscription_error(subscription, error):
    subscription.errors.append(error)
    subscription.status_id = subscription_status.error.id
    subscription.checked = get_current_time()
    subscription.requery = None
    commit_session()


def delay_subscription_elements(subscription, delay_days):
    current_time = get_current_time()
    for element in subscription.undecided_elements:
        if delay_days == 0:
            element.expires = None
        else:
            element.expires = add_days(max(element.expires or current_time, current_time), delay_days)
    commit_session()


def get_average_interval_for_subscriptions(subscriptions, days):
    subscription_ids = [s.id for s in subscriptions]
    undecided_count_cte = SubscriptionElement.query.filter(SubscriptionElement.subscription_id.in_(subscription_ids))\
                                                   .group_by(SubscriptionElement.subscription_id)\
                                                   .with_entities(SubscriptionElement.subscription_id,
                                                                  COUNT_UNDECIDED_ELEMENTS,
                                                                  )\
                                                   .cte()
    average_interval_clause = (func.iif(undecided_count_cte.c.count == 0,
                                        Subscription.checked - func.min(Illust.site_created),
                                        func.max(Illust.site_created) - func.min(Illust.site_created))
                               ) / DISTINCT_ILLUST_COUNT
    keep_filter = SubscriptionElement.keep_filter('name', '__eq__', 'yes')
    return SubscriptionElement.query.enum_join(SubscriptionElement.keep_enum)\
                              .join(Subscription).join(IllustUrl).join(Illust).join(undecided_count_cte)\
                              .with_entities(SubscriptionElement.subscription_id, average_interval_clause)\
                              .filter(SubscriptionElement.subscription_id.in_([s.id for s in subscriptions]),
                                      Illust.site_created > days_ago(days),
                                      keep_filter,
                                      )\
                              .group_by(SubscriptionElement.subscription_id)\
                              .having(DISTINCT_ILLUST_COUNT > 0).all()
