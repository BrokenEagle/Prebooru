# APP/LOGICAL/DATABASE/SUBSCRIPTION_POOL_ELEMENT_DB.PY

# ## LOCAL IMPORTS
from ...models import SubscriptionPoolElement
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
