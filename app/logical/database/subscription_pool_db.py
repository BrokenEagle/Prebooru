# APP/LOGICAL/DATABASE/SUBSCRIPTION_POOL_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time, hours_from_now, add_days

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import SubscriptionPool
from .base_db import update_column_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['artist_id', 'interval', 'expiration', 'last_id', 'requery', 'checked', 'active']

CREATE_ALLOWED_ATTRIBUTES = ['artist_id', 'interval', 'expiration', 'active']
UPDATE_ALLOWED_ATTRIBUTES = ['interval', 'expiration', 'active']

MAXIMUM_PROCESS_SUBSCRIPTIONS = 10


# ## FUNCTIONS

# #### Route DB functions

# ###### Create

def create_subscription_pool_from_parameters(createparams):
    current_time = get_current_time()
    pool = SubscriptionPool(status='idle', created=current_time, updated=current_time)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(pool, update_columns, createparams)
    print("[%s]: created" % pool.shortlink)
    return pool


# ###### Update

def update_subscription_pool_from_parameters(pool, updateparams):
    update_results = []
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(update_column_attributes(pool, update_columns, updateparams))
    if pool.requery is not None and pool.requery > hours_from_now(pool.interval):
        update_subscription_pool_requery(pool, hours_from_now(pool.interval))
    if any(update_results):
        print("[%s]: updated" % pool.shortlink)
        pool.updated = get_current_time()
        SESSION.commit()


def update_subscription_pool_status(pool, status):
    pool.status = status
    SESSION.commit()


def update_subscription_pool_active(pool, active):
    pool.active = active
    SESSION.commit()


def update_subscription_pool_requery(pool, timeval):
    pool.requery = timeval
    SESSION.commit()


def update_subscription_pool_last_info(pool, last_id):
    pool.last_id = last_id
    pool.checked = get_current_time()
    SESSION.commit()


# ###### Delete

def delete_subscription_pool(pool):
    SESSION.delete(pool)
    SESSION.commit()


# #### Query

def get_available_subscription(unlimited):
    # Return only subscriptions which have already been processed manually (requery is not None)
    query = SubscriptionPool.query.filter(SubscriptionPool.requery < get_current_time(),
                                          SubscriptionPool.active.is_(True),
                                          SubscriptionPool.status.not_in(['manual', 'automatic']))
    if not unlimited:
        query = query.limit(MAXIMUM_PROCESS_SUBSCRIPTIONS)
    return query.all()


def check_processing_subscriptions():
    return SubscriptionPool.query.filter_by(status='manual').get_count() > 0


# #### Misc

def add_subscription_pool_error(pool, error):
    pool.errors.append(error)
    pool.status = 'error'
    pool.checked = get_current_time()
    pool.requery = None
    pool.active = False
    SESSION.commit()


def delay_subscription_pool_elements(subscription_pool, delay_days):
    current_time = get_current_time()
    for element in subscription_pool.active_elements:
        if element.keep == 'maybe':
            continue
        if delay_days == 0:
            element.expires = None
        else:
            element.expires = add_days(max(element.expires or current_time, current_time), delay_days)
    SESSION.commit()
