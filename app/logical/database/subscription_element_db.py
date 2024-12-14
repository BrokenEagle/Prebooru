# APP/LOGICAL/DATABASE/SUBSCRIPTION_ELEMENT_DB.PY

# ## PYTHON IMPORTS
import os

# ## EXTERNAL IMPORTS
from sqlalchemy import and_, or_

# ## PACKAGE IMPORTS
from config import EXPIRED_SUBSCRIPTION, ALTERNATE_MEDIA_DIRECTORY
from utility.time import days_from_now, get_current_time

# ## LOCAL IMPORTS
from ...enum_imports import subscription_element_status, subscription_element_keep
from ...models import Subscription, SubscriptionElement, Post
from ..records.post_rec import archive_post_for_deletion, delete_post_and_media
from .base_db import set_column_attributes, save_record, commit_session


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

# #### Route DB functions

# ###### CREATE

def create_subscription_element_from_parameters(createparams):
    subscription_element = SubscriptionElement(status_id=subscription_element_status.active.id)
    set_column_attributes(subscription_element, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, createparams)
    save_record(subscription_element, 'created')
    return subscription_element


# ###### UPDATE

def batch_update_subscription_element_keep(subscription_elements, value):
    for subscription_element in subscription_elements:
        _update_subscription_element_keep(subscription_element, value)
    commit_session()


def update_subscription_element_keep(subscription_element, value):
    _update_subscription_element_keep(subscription_element, value)
    commit_session()


def update_subscription_element_status(subscription_element, value):
    subscription_element.status_id = subscription_element_status.by_name(value).id
    commit_session()


# #### Misc

def link_subscription_post(element, post):
    element.post = post
    element.md5 = post.md5
    element.status_id = subscription_element_status.active.id
    element.expires = None
    _update_subscription_element_keep(element, None)
    commit_session()


def unlink_subscription_post(element):
    element.post = None
    element.expires = None
    element.status_id = subscription_element_status.unlinked.id
    commit_session()


def delete_subscription_post(element):
    if element.post is not None:
        if element.post.alternate and not os.path.exists(ALTERNATE_MEDIA_DIRECTORY):
            return False
        delete_post_and_media(element.post)
    element.expires = None
    element.status_id = subscription_element_status.deleted.id
    commit_session()
    return True


def archive_subscription_post(element):
    if element.post is not None:
        if element.post.alternate and not os.path.exists(ALTERNATE_MEDIA_DIRECTORY):
            return False
        archive_post_for_deletion(element.post, None)
    element.expires = None
    element.status_id = subscription_element_status.archived.id
    commit_session()


def duplicate_subscription_post(element, md5):
    element.expires = None
    element.md5 = md5
    element.status_id = subscription_element_status.duplicate.id
    element.keep_id = subscription_element_keep.unknown.id
    commit_session()


# #### Query

def get_elements_by_id(id_list):
    return SubscriptionElement.query.filter(SubscriptionElement.id.in_(id_list)).all()


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
