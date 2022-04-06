# APP/LOGICAL/DATABASE/TAG_DB.PY

# ## LOCAL IMPORTS
from ...models import SiteTag, UserTag
from .base_db import update_column_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['name']
TAG_MODEL_DICT = {
    'site_tag': SiteTag,
    'user_tag': UserTag,
}

# ## FUNCTIONS

def create_tag_from_parameters(createparams):
    update_columns = set(createparams.keys()).intersection(COLUMN_ATTRIBUTES)
    tag = TAG_MODEL_DICT[createparams['type']]()
    update_column_attributes(tag, update_columns, createparams)
    return tag

