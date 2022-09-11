# APP/LOGICAL/DATABASE/SUBSCRIPTION_ELEMENT_DB.PY

# ## PACKAGE IMPORTS
from utility.time import days_from_now, get_current_time

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Subscription, SubscriptionElement
from ..records.post_rec import archive_post_for_deletion, delete_post_and_media
from .base_db import update_column_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['subscription_id', 'illust_url_id', 'post_id', 'expires']

CREATE_ALLOWED_ATTRIBUTES = ['subscription_id', 'illust_url_id', 'post_id', 'expires']


# ## FUNCTIONS

# #### Route DB functions

# ###### CREATE

def create_subscription_element_from_parameters(createparams):
    subscription_element = SubscriptionElement(active=True, deleted=False, status='active')
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(subscription_element, update_columns, createparams)
    print("[%s]: created" % subscription_element.shortlink)
    return subscription_element


# ###### UPDATE

def update_subscription_element_active(subscription_element, active):
    subscription_element.active = active
    SESSION.commit()


def update_subscription_element_deleted(subscription_element, deleted):
    subscription_element.deleted = deleted
    SESSION.commit()


def batch_update_subscription_element_keep(subscription_elements, value):
    for subscription_element in subscription_elements:
        _update_subscription_element_keep(subscription_element, value)
    SESSION.commit()


def update_subscription_element_keep(subscription_element, value):
    _update_subscription_element_keep(subscription_element, value)
    SESSION.commit()


def update_subscription_element_status(subscription_element, value):
    subscription_element.status = value
    SESSION.commit()


# #### Misc

def link_subscription_post(element, post):
    element.post = post
    element.active = True
    element.md5 = post.md5
    element.status = 'active'
    element.expires = None
    _update_subscription_element_keep(element, None)
    SESSION.commit()


def unlink_subscription_post(element):
    element.post = None
    element.expires = None
    element.active = False
    element.status = 'unlinked'
    SESSION.commit()


def delete_subscription_post(element):
    if element.post is not None:
        delete_post_and_media(element.post)
    element.expires = None
    element.active = False
    element.deleted = True
    element.status = 'deleted'
    SESSION.commit()


def archive_subscription_post(element):
    if element.post is not None:
        archive_post_for_deletion(element.post, None)
    element.expires = None
    element.active = False
    element.deleted = True
    element.status = 'archived'
    SESSION.commit()


def duplicate_subscription_post(element, md5):
    element.expires = None
    element.active = False
    element.md5 = md5
    element.status = 'duplicate'
    SESSION.commit()


# #### Query

def get_elements_by_id(id_list):
    return SubscriptionElement.query.filter(SubscriptionElement.id.in_(id_list)).all()


def check_deleted_subscription_post(md5):
    return SESSION.query(SubscriptionElement.id).filter_by(md5=md5, deleted=True).first() is not None


def total_expired_subscription_elements():
    return SubscriptionElement.query.filter(SubscriptionElement.expires < get_current_time(),
                                                SubscriptionElement.post_id.is_not(None)).get_count()


def total_missing_downloads():
    return SubscriptionElement.query.join(Subscription)\
                                        .filter(SubscriptionElement.post_id.is_(None),
                                                SubscriptionElement.active.is_(True),
                                                SubscriptionElement.deleted.is_(False),
                                                Subscription.status == 'idle')\
                                        .get_count()


# #### Private

def _update_subscription_element_keep(element, value):
    element.keep = value
    if value == 'yes' or value == 'archive':
        element.expires = days_from_now(1)  # Posts will be unlinked/archived after this period
    elif value == 'no':
        element.expires = days_from_now(7)  # Posts will be deleted after this period
    elif value == 'maybe':
        element.expires = None  # Keep the element around until/unless a decision is made on it
    elif value is None:
        element.expires = days_from_now(element.subscription.expiration)  # Reset the expiration
