# APP/LOGICAL/DATABASE/SUBSCRIPTION_ELEMENT_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import and_, or_

# ## PACKAGE IMPORTS
from config import EXPIRED_SUBSCRIPTION
from utility.time import days_from_now, get_current_time

# ## LOCAL IMPORTS
from ... import SESSION
from ...enum_imports import subscription_element_status, subscription_element_keep
from ...models import Subscription, SubscriptionElement, Post, MediaAsset
from ..records.post_rec import archive_post_for_deletion, delete_post_and_media
from .base_db import set_column_attributes, commit_or_flush


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['status_id', 'keep_id', 'post_id', 'expires']
NULL_WRITABLE_ATTRIBUTES = ['subscription_id', 'illust_url_id', 'media_asset_id']

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
    return set_subscription_element_from_parameters(Subscription(status_id=subscription_element_status.active.id),
                                                    createparams, commit, 'created')


# ###### Update

def update_subscription_element_from_parameters(subscription_element, updateparams, commit=True):
    expires = False
    if 'keep' in updateparams:
        updateparams['keep_id'] = subscription_element_keep.by_name(updateparams['keep']).id
        expires = _get_keep_expires(subscription_element, updateparams['keep'])
    elif 'keep_id' in updateparams:
        expires = _get_keep_expires(subscription_element, subscription_element_keep.by_id(updateparams['keep_id']).name)
    if expires is not False:
        updateparams['expires'] = expires
    return set_subscription_element_from_parameters(subscription_element, updateparams, commit, 'updated')


# #### Set

def set_subscription_element_from_parameters(subscription_element, setparams, commit, action):
    if 'status' in setparams:
        setparams['status_id'] = subscription_element_status.by_name(setparams['status']).id
    if set_column_attributes(subscription_element, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        commit_or_flush(commit)
        print("[%s]: %s" % (subscription_element.shortlink, action))
    return subscription_element


# #### Misc

def link_subscription_post(element, post):
    updateparams = {
        'post_id': post.id,
        'media_asset_id': post.media_asset_id,
        'keep': None,
        'status': 'active',
    }
    update_subscription_element_from_parameters(element, updateparams)


def unlink_subscription_post(element):
    element.expires = None
    updateparams = {
        'post_id': None,
        'expires': None,
        'status': 'unlinked',
    }
    update_subscription_element_from_parameters(element, updateparams)


def delete_subscription_post(element):
    if element.post is not None:
        delete_post_and_media(element.post)
    updateparams = {
        'post_id': None,
        'expires': None,
        'status': 'deleted',
    }
    update_subscription_element_from_parameters(element, updateparams)


def archive_subscription_post(element):
    if element.post is not None:
        if not element.media.has_file_access:
            return False
        archive_post_for_deletion(element.post, None)
    update_subscription_element_from_parameters(element, {'keep': 'archived'})


def duplicate_subscription_post(element, media_asset_id):
    updateparams = {
        'media_asset_id': media_asset_id,
        'status': 'duplicate',
        'keep': 'unknown',
    }
    update_subscription_element_from_parameters(element, updateparams)


# #### Query

def get_elements_by_id(id_list):
    return SubscriptionElement.query.filter(SubscriptionElement.id.in_(id_list)).all()


def get_elements_by_md5(md5):
    return SubscriptionElement.query.join(MediaAsset).filter(MediaAsset.md5 == md5).all()


def check_deleted_subscription_post(md5):
    return SESSION.query(SubscriptionElement.id)\
                  .join(MediaAsset)\
                  .filter(MediaAsset.md5 == md5,
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
    elif value == 'maybe' or value == 'unknown':
        element.expires = None  # Keep the element around until/unless a decision is made on it
    elif value is None:
        element.expires = days_from_now(element.subscription.expiration)  # Reset the expiration


def _get_keep_expires(element, value):
    if value == 'yes' or value == 'archive':
        # Posts will be unlinked/archived after this period
        return days_from_now(1)
    elif value == 'no':
        # Posts will be deleted after this period
        return days_from_now(7)
    elif value == 'maybe' or value == 'unknown':
        # Keep the element around until/unless a decision is made on it
        return None
    elif value is None:
        # Reset the expiration
        return days_from_now(element.subscription.expiration)
    return False


def _expired_clause(keep, action):
    main_clause = SubscriptionElement.keep_filter('name', '__eq__', keep)
    if (action == EXPIRED_SUBSCRIPTION_ACTION):
        keep_clause = or_(main_clause, SubscriptionElement.keep_filter('name', 'is_', None))
    else:
        keep_clause = main_clause
    return and_(SubscriptionElement.expires < get_current_time(),
                SubscriptionElement.status_filter('name', '__eq__', 'active'), keep_clause)
