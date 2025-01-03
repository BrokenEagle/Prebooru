# APP/LOGICAL/DATABASE/SUBSCRIPTION_ELEMENT_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import and_, or_

# ## PACKAGE IMPORTS
from config import EXPIRED_SUBSCRIPTION
from utility.time import days_from_now, get_current_time

# ## LOCAL IMPORTS
from ...enum_imports import subscription_element_status, subscription_element_keep
from ...models import Subscription, SubscriptionElement, Post
from .base_db import set_column_attributes, save_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['status_id', 'keep_id', 'post_id', 'expires']
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
    subscription_element = SubscriptionElement(status_id=subscription_element_status.active.id)
    return set_subscription_element_from_parameters(subscription_element, createparams, 'created', commit)


# #### Update

def update_subscription_element_from_parameters(subscription_element, updateparams, commit=True):
    return set_subscription_element_from_parameters(subscription_element, updateparams, 'updated', commit)


# #### Set

def set_subscription_element_from_parameters(subscription_element, setparams, action, commit):
    if 'status' in setparams:
        setparams['status_id'] = SubscriptionElement.status_enum.by_name(setparams['status']).id
    if 'keep' in setparams:
        setparams['keep_id'] = SubscriptionElement.keep_enum.by_name(setparams['keep']).id
    if set_column_attributes(subscription_element, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(subscription_element, action, commit=commit)
    return subscription_element


# #### Query

def get_elements_by_id(id_list):
    return SubscriptionElement.query.filter(SubscriptionElement.id.in_(id_list)).all()


def get_subscription_elements_by_md5(md5):
    return SubscriptionElement.query\
                              .filter(SubscriptionElement.md5 == md5)\
                              .all()


def check_deleted_subscription_post(md5):
    return SubscriptionElement.query.enum_join(SubscriptionElement.status_enum)\
                              .filter(SubscriptionElement.md5 == md5,
                                      SubscriptionElement.status_filter('name', 'in_', ['deleted', 'archived']))\
                              .with_entities(SubscriptionElement.id)\
                              .first() is not None


def expired_subscription_elements(expire_type):
    switcher = {
        'unlink': lambda q: q.join(Post, SubscriptionElement.post)
                             .filter(or_(_expired_clause('yes', 'unlink'), Post.type_filter('name', '__eq__', 'user'))),
        'delete': lambda q: q.filter(_expired_clause('no', 'delete')),
        'archive': lambda q: q.filter(_expired_clause('archive', 'archive')),
    }
    query = SubscriptionElement.query.filter(SubscriptionElement.expires < get_current_time(),
                                             SubscriptionElement.post_id.is_not(None))
    return switcher[expire_type](query)


def pending_subscription_downloads_query():
    return SubscriptionElement.query.join(Subscription)\
                                    .filter(SubscriptionElement.post_id.is_(None),
                                            SubscriptionElement.status_filter('name', '__eq__', 'active'),
                                            Subscription.status_filter('name', 'not_in', ['automatic', 'manual']))


def total_missing_downloads():
    return pending_subscription_downloads_query().get_count()


# #### Private

def _update_subscription_element_keep(element, value):
    element.keep_id = subscription_element_keep.by_name(value).id if value is not None else None
    if value == 'yes' or value == 'archive':
        element.expires = days_from_now(1)  # Posts will be unlinked/archived after this period
    elif value == 'no':
        element.expires = days_from_now(7)  # Posts will be deleted after this period
    elif value == 'maybe' or value == 'unknown':
        element.expires = None  # Keep the element around until/unless a decision is made on it
    elif value is None:
        element.expires = days_from_now(element.subscription.expiration)  # Reset the expiration


def _expired_clause(keep, action):
    main_clause = SubscriptionElement.keep_filter('name', '__eq__', keep)
    if (action == EXPIRED_SUBSCRIPTION_ACTION):
        keep_clause = or_(main_clause, SubscriptionElement.keep_filter('name', 'is_', None))
    else:
        keep_clause = main_clause
    return and_(SubscriptionElement.expires < get_current_time(),
                SubscriptionElement.status_filter('name', '__eq__', 'active'), keep_clause)
