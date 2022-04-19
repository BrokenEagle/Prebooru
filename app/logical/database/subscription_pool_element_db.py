# APP/LOGICAL/DATABASE/SUBSCRIPTION_POOL_ELEMENT_DB.PY

# ## PACKAGE IMPORTS
from utility.time import days_from_now, get_current_time

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import SubscriptionPoolElement
from ..records.post_rec import archive_post_for_deletion
from .post_db import delete_post
from .base_db import update_column_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['pool_id', 'illust_url_id', 'post_id', 'expires']

CREATE_ALLOWED_ATTRIBUTES = ['pool_id', 'illust_url_id', 'post_id', 'expires']


# ## FUNCTIONS

# #### Route DB functions

# ###### CREATE

def create_subscription_pool_element_from_parameters(createparams):
    subscription_pool_element = SubscriptionPoolElement(active=True, deleted=False)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(subscription_pool_element, update_columns, createparams)
    print("[%s]: created" % subscription_pool_element.shortlink)
    return subscription_pool_element


# ###### UPDATE

def update_subscription_pool_element_active(subscription_pool_element, active):
    subscription_pool_element.active = active
    SESSION.commit()


def update_subscription_pool_element_keep(subscription_pool_element, value):
    subscription_pool_element.keep = value
    if value == 'yes':
        subscription_pool_element.expires = days_from_now(1)  # Posts will be unlinked after this period
    elif value == 'maybe':
        subscription_pool_element.expires = None  # Will force the expires to be refreshed when changed
    elif subscription_pool_element.expires is None:
        subscription_pool_element.expires = days_from_now(subscription_pool_element.pool.expiration)
    SESSION.commit()


# #### Misc

def unlink_subscription_post(element):
    element.post_id = None
    element.expires = None
    element.active = False
    SESSION.commit()


def delete_subscription_post(element):
    if element.post is not None:
        delete_post(element.post)
    element.expires = None
    element.active = False
    element.deleted = True
    SESSION.commit()


def archive_subscription_post(element):
    if element.post is not None:
        archive_post_for_deletion(element.post)
    element.expires = None
    element.active = False
    element.deleted = True
    SESSION.commit()


def add_subscription_post(subscription_pool_element, post):
    subscription_pool_element.post_id = post.id
    subscription_pool_element.md5 = post.md5
    SESSION.commit()


# #### Query

def get_elements_by_id(id_list):
    return SubscriptionPoolElement.query.filter(SubscriptionPoolElement.id.in_(id_list)).all()


def check_deleted_subscription_post(md5):
    return SESSION.query(SubscriptionPoolElement.id).filter_by(md5=md5, deleted=True).first() is not None


def total_expired_subscription_elements():
    return SubscriptionPoolElement.query.filter(SubscriptionPoolElement.expires < get_current_time(),
                                                SubscriptionPoolElement.post_id.is_not(None)).get_count()


def total_missing_downloads():
    return SubscriptionPoolElement.query.filter_by(post_id=None, active=True, deleted=False).get_count()
