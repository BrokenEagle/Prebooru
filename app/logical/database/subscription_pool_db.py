# APP/LOGICAL/DATABASE/SUBSCRIPTION_POOL_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import SubscriptionPool
from .base_db import update_column_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['artist_id', 'interval', 'expiration', 'last_id', 'requery', 'checked', 'active']

CREATE_ALLOWED_ATTRIBUTES = ['artist_id', 'interval', 'expiration', 'active']
UPDATE_ALLOWED_ATTRIBUTES = ['interval', 'expiration', 'active']


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
    if any(update_results):
        print("[%s]: updated" % pool.shortlink)
        pool.updated = get_current_time()
        SESSION.commit()


def update_subscription_pool_status(pool, status):
    pool.status = status
    SESSION.commit()


def update_subscription_pool_active(pool, status):
    pool.status = status
    SESSION.commit()


def update_subscription_pool_requery(pool, timeval):
    pool.requery = timeval
    SESSION.commit()


def update_subscription_pool_last_info(pool, last_id):
    pool.last_id = last_id
    pool.checked = get_current_time()
    SESSION.commit()


# #### Query

def get_available_subscription():
    # Return only subscriptions which have already been processed manually (requery is not None)
    return SubscriptionPool.query.filter(SubscriptionPool.requery < get_current_time(),
                                         SubscriptionPool.active.__eq__(True)).limit(20).all()


# #### Misc

def add_subscription_pool_error(pool, error):
    pool.errors.append(error)
    pool.checked = get_current_time()
    pool.requery = None
    pool.active = False
    SESSION.commit()
