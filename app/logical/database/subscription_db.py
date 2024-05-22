# APP/LOGICAL/DATABASE/SUBSCRIPTION_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import func

# ## PACKAGE IMPORTS
from utility.time import get_current_time, hours_from_now, add_days, days_ago

# ## LOCAL IMPORTS
from ...enum_imports import subscription_status
from ...models import Subscription, SubscriptionElement, IllustUrl, Illust
from .base_db import set_column_attributes, commit_or_flush, save_record, delete_record
from .error_db import append_error


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['interval', 'expiration']
NULL_WRITABLE_ATTRIBUTES = ['artist_id']


DISTINCT_ILLUST_COUNT = func.count(Illust.id.distinct())
UNDECIDED_COUNT = func.count(SubscriptionElement.keep_filter('id', 'is_', None))
DISTINCT_ELEMENT_COUNT = func.count(SubscriptionElement.id.distinct())
COUNT_UNDECIDED_ELEMENTS = func.sum(func.iif(SubscriptionElement.keep_filter('id', 'is_', None), 1, 0)).label('count')


# ## FUNCTIONS

# #### Create

def create_subscription_from_parameters(createparams, commit=True):
    return set_subscription_from_parameters(Subscription(status_id=subscription_status.idle.id),
                                            createparams, commit, 'created', False)


# #### Update

def update_subscription_from_parameters(subscription, updateparams, commit=True, update=False):
    return set_subscription_from_parameters(subscription, updateparams, commit, 'updated', update)


# #### Set

def set_subscription_from_parameters(subscription, setparams, commit, action, update):
    if set_column_attributes(subscription, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams, update):
        # Will only be modified when lowering the interval
        expected_requery = hours_from_now(subscription.interval)
        if subscription.requery is not None and subscription.requery > expected_requery:
            subscription.requery = expected_requery
        save_record(subscription, commit, action)
    return subscription


# ###### Delete

def delete_subscription(subscription):
    delete_record(subscription)
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
    append_error(subscription, error, commit=False)
    updateparams = {'status': 'error', 'checked': get_current_time(), 'requery': None}
    update_subscription_from_parameters(subscription, updateparams, commit=True)


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
