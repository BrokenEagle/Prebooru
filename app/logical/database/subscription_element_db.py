# APP/LOGICAL/DATABASE/SUBSCRIPTION_ELEMENT_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import and_, or_

# ## PACKAGE IMPORTS
from config import EXPIRED_SUBSCRIPTION
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ...models import Subscription, SubscriptionElement, Post
from .base_db import set_column_attributes, save_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_ATTRIBUTES = ['status_name', 'keep_name', 'post_id', 'expires']
NULL_WRITABLE_ATTRIBUTES = ['subscription_id', 'illust_url_id', 'md5']

if EXPIRED_SUBSCRIPTION is True:
    EXPIRED_SUBSCRIPTION_ACTION = 'archive'
elif EXPIRED_SUBSCRIPTION in ['unlink', 'delete', 'archive']:
    EXPIRED_SUBSCRIPTION_ACTION = EXPIRED_SUBSCRIPTION
elif EXPIRED_SUBSCRIPTION is False:
    EXPIRED_SUBSCRIPTION_ACTION = None
else:
    raise ValueError("Bad value set in config for EXPIRED_SUBSCRIPTION.")


# ## FUNCTIONS

# #### Create

def create_subscription_element_from_parameters(createparams, commit=True):
    createparams.setdefault('status_name', 'active')
    return set_subscription_element_from_parameters(SubscriptionElement(), createparams, 'created', commit)


# #### Update

def update_subscription_element_from_parameters(subscription_element, updateparams, commit=True):
    return set_subscription_element_from_parameters(subscription_element, updateparams, 'updated', commit)


# #### Set

def set_subscription_element_from_parameters(subscription_element, setparams, action, commit):
    if set_column_attributes(subscription_element, ANY_WRITABLE_ATTRIBUTES, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(subscription_element, action, commit=commit)
    return subscription_element


# #### Query

def get_elements_by_id(id_list):
    return SubscriptionElement.query.filter(SubscriptionElement.id.in_(id_list)).all()


def get_subscription_elements_by_md5(md5):
    return SubscriptionElement.query\
                              .filter(SubscriptionElement.md5 == md5)\
                              .all()


def expired_subscription_elements(expire_type):
    switcher = {
        'unlink': lambda q: q.join(Post, SubscriptionElement.post)
                             .filter(or_(_expired_clause('yes', 'unlink'), Post.type_value == 'user')),
        'delete': lambda q: q.filter(_expired_clause('no', 'delete')),
        'archive': lambda q: q.filter(_expired_clause('archive', 'archive')),
    }
    query = SubscriptionElement.query.filter(SubscriptionElement.expires < get_current_time(),
                                             SubscriptionElement.post_id.is_not(None))
    return switcher[expire_type](query)


def pending_subscription_downloads_query():
    return SubscriptionElement.query.join(Subscription)\
                                    .filter(SubscriptionElement.post_id.is_(None),
                                            SubscriptionElement.status_value == 'active',
                                            Subscription.status_value.not_in(['automatic', 'manual']))


def total_missing_downloads():
    return pending_subscription_downloads_query().get_count()


# #### Private

def _expired_clause(keep, action):
    if (action == EXPIRED_SUBSCRIPTION_ACTION):
        keep_clause = or_(SubscriptionElement.keep_value == keep, SubscriptionElement.keep_value.is_(None))
    else:
        keep_clause = SubscriptionElement.keep_value == keep
    return and_(SubscriptionElement.expires < get_current_time(),
                SubscriptionElement.status_value == 'active',
                keep_clause)
