# APP/LOGICAL/DATABASE/SUBSCRIPTION_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import func

# ## PACKAGE IMPORTS
from utility.time import get_current_time, hours_from_now, add_days, days_ago

# ## LOCAL IMPORTS
from ...enum_imports import subscription_status
from ...models import Subscription, SubscriptionElement, IllustUrl, Illust
from .base_db import set_column_attributes, commit_or_flush


# ## GLOBAL VARIABLES

CREATE_ALLOWED_ATTRIBUTES = ['artist_id', 'interval', 'expiration']
UPDATE_ALLOWED_ATTRIBUTES = ['interval', 'expiration']

DISTINCT_ILLUST_COUNT = func.count(Illust.id.distinct())
UNDECIDED_COUNT = func.count(SubscriptionElement.keep_filter('id', 'is_', None))
DISTINCT_ELEMENT_COUNT = func.count(SubscriptionElement.id.distinct())
COUNT_UNDECIDED_ELEMENTS = func.sum(func.iif(SubscriptionElement.keep_filter('id', 'is_', None), 1, 0)).label('count')


# ## FUNCTIONS

# #### Route DB functions

# ###### Create

def create_subscription_from_parameters(createparams, commit=True):
    if 'status' in createparams:
        createparams['status_id'] = Subscription.status_enum.by_name(createparams['status']).id
    current_time = get_current_time()
    subscription = Subscription(status_id=subscription_status.idle.id, created=current_time, updated=current_time)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(Subscription.all_columns)
    set_column_attributes(subscription, update_columns, createparams)
    commit_or_flush(commit)
    print("[%s]: created" % subscription.shortlink)
    return subscription


# ###### Update

def update_subscription_from_parameters(subscription, updateparams, commit=True):
    if 'status' in updateparams:
        updateparams['status_id'] = Subscription.status_enum.by_name(updateparams['status']).id
    update_results = []
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(Subscription.all_columns)
    update_results.append(set_column_attributes(subscription, update_columns, updateparams))
    if subscription.requery is not None and subscription.requery > hours_from_now(subscription.interval):
        update_subscription_requery(subscription, hours_from_now(subscription.interval))
    if any(update_results):
        subscription.updated = get_current_time()
        commit_or_flush(commit)
        print("[%s]: updated" % subscription.shortlink)
    return subscription


def update_subscription_status(subscription, value):
    subscription.status_id = subscription_status.by_name(value).id
    commit_or_flush(True)


def update_subscription_requery(subscription, timeval):
    subscription.requery = timeval
    commit_or_flush(True)


def update_subscription_last_info(subscription):
    subscription.checked = get_current_time()
    commit_or_flush(True)


# ###### Delete

def delete_subscription(subscription):
    SESSION.delete(subscription)
    commit_or_flush(True)


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
    commit_or_flush(True)


def delay_subscription_elements(subscription, delay_days):
    current_time = get_current_time()
    for element in subscription.undecided_elements:
        if delay_days == 0:
            element.expires = None
        else:
            element.expires = add_days(max(element.expires or current_time, current_time), delay_days)
    commit_or_flush(True)


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
