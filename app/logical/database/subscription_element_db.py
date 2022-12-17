# APP/LOGICAL/DATABASE/SUBSCRIPTION_ELEMENT_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import and_, or_

# ## PACKAGE IMPORTS
from config import EXPIRED_SUBSCRIPTION
from utility.time import days_from_now, get_current_time

# ## LOCAL IMPORTS
from ... import SESSION
from ...enum_imports import subscription_element_status, subscription_element_keep
from ...models import Subscription, SubscriptionElement, Post
from ..records.post_rec import archive_post_for_deletion, delete_post_and_media
from .base_db import update_column_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['subscription_id', 'illust_url_id', 'post_id', 'expires']

CREATE_ALLOWED_ATTRIBUTES = ['subscription_id', 'illust_url_id', 'post_id', 'expires']

if EXPIRED_SUBSCRIPTION is True:
    EXPIRED_SUBSCRIPTION_ACTION = 'archive'
elif EXPIRED_SUBSCRIPTION in ['unlink', 'delete', 'archive']:
    EXPIRED_SUBSCRIPTION_ACTION = EXPIRED_SUBSCRIPTION
elif EXPIRED_SUBSCRIPTION is False:
    EXPIRED_SUBSCRIPTION_ACTION = None
else:
    raise ValueError("Bad value set in config for EXPIRED_SUBSCRIPTION.")


# ## FUNCTIONS

# #### Route DB functions

# ###### CREATE

def create_subscription_element_from_parameters(createparams):
    subscription_element = SubscriptionElement(status_id=subscription_element_status.active.id)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(subscription_element, update_columns, createparams)
    print("[%s]: created" % subscription_element.shortlink)
    return subscription_element


# ###### UPDATE

def batch_update_subscription_element_keep(subscription_elements, value):
    for subscription_element in subscription_elements:
        _update_subscription_element_keep(subscription_element, value)
    SESSION.commit()


def update_subscription_element_keep(subscription_element, value):
    _update_subscription_element_keep(subscription_element, value)
    SESSION.commit()


def update_subscription_element_status(subscription_element, value):
    subscription_element.status_id = subscription_element_status.by_name(value).id
    SESSION.commit()


# #### Misc

def link_subscription_post(element, post):
    element.post = post
    element.md5 = post.md5
    element.status_id = subscription_element_status.active.id
    element.expires = None
    _update_subscription_element_keep(element, None)
    SESSION.commit()


def unlink_subscription_post(element):
    element.post = None
    element.expires = None
    element.status_id = subscription_element_status.unlinked.id
    SESSION.commit()


def delete_subscription_post(element):
    if element.post is not None:
        delete_post_and_media(element.post)
    element.expires = None
    element.status_id = subscription_element_status.deleted.id
    SESSION.commit()


def archive_subscription_post(element):
    if element.post is not None:
        archive_post_for_deletion(element.post, None)
    element.expires = None
    element.status_id = subscription_element_status.archived.id
    SESSION.commit()


def duplicate_subscription_post(element, md5):
    element.expires = None
    element.md5 = md5
    element.status_id = subscription_element_status.duplicate.id
    SESSION.commit()


# #### Query

def get_elements_by_id(id_list):
    return SubscriptionElement.query.filter(SubscriptionElement.id.in_(id_list)).all()


def check_deleted_subscription_post(md5):
    return SESSION.query(SubscriptionElement.id)\
                  .filter(SubscriptionElement.md5 == md5,
                          SubscriptionElement.status_filter('name', 'in_', ['deleted', 'archived'])
                          ).first() is not None


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
                                            Subscription.status_filter('name', '__eq__', 'idle'))


def total_missing_downloads():
    return SubscriptionElement.query.join(Subscription)\
                                    .filter(SubscriptionElement.post_id.is_(None),
                                            SubscriptionElement.status_filter('name', '__eq__', 'active'),
                                            Subscription.status_filter('name', '__eq__', 'idle'))\
                                    .get_count()


# #### Private

def _update_subscription_element_keep(element, value):
    element.keep_id = subscription_element_keep.by_name(value).id if value is not None else None
    if value == 'yes' or value == 'archive':
        element.expires = days_from_now(1)  # Posts will be unlinked/archived after this period
    elif value == 'no':
        element.expires = days_from_now(7)  # Posts will be deleted after this period
    elif value == 'maybe':
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
