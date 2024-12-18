# APP/LOGICAL/DATABASE/TAG_DB.PY

# ## LOCAL IMPORTS
from ...models import SiteTag, UserTag
from .base_db import set_column_attributes, save_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['name']
NULL_WRITABLE_ATTRIBUTES = []

TAG_MODEL_DICT = {
    'site_tag': SiteTag,
    'user_tag': UserTag,
}


# ## FUNCTIONS

# #### Create

def create_tag_from_parameters(createparams, commit=True):
    tag = TAG_MODEL_DICT[createparams['type']]()
    return set_tag_from_parameters(tag, createparams, 'created', commit)


# #### Set

def set_tag_from_parameters(tag, setparams, action, commit):
    if set_column_attributes(tag, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(tag, action, commit=commit)
    return tag


# #### Query

def get_tags_by_names(names, type):
    model = TAG_MODEL_DICT[type]
    return model.query.filter(model.name.in_(names)).all()
