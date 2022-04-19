# APP/LOGICAL/DATABASE/TAG_DB.PY

# ## PACKAGE IMPORTS


# ## LOCAL IMPORTS
from ... import SESSION
from ...models import SiteTag, UserTag, Post
from ..utility import set_error
from .base_db import update_column_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['name']
TAG_MODEL_DICT = {
    'site_tag': SiteTag,
    'user_tag': UserTag,
}

ID_MODEL_DICT = {
    'post_id': Post,
}


# ## FUNCTIONS

def create_tag_from_parameters(createparams):
    update_columns = set(createparams.keys()).intersection(COLUMN_ATTRIBUTES)
    tag = TAG_MODEL_DICT[createparams['type']]()
    update_column_attributes(tag, update_columns, createparams)
    return tag


def append_tag_to_item(tag, append_key, dataparams):
    retdata = {'error': False}
    model = ID_MODEL_DICT[append_key]
    item = model.find(dataparams[append_key])
    table_name = model.__table__.name
    if item is None:
        msg = "Unable to append tag; %s #%d does not exist." % (table_name, dataparams[append_key])
        return set_error(retdata, msg)
    elif tag in item._tags:
        return set_error(retdata, "Tag '%s' already added to %s." % (tag.name, item.shortlink))
    item._tags.append(tag)
    SESSION.commit()
    return retdata


def remove_tag_from_item(tag, remove_key, dataparams):
    retdata = {'error': False}
    model = ID_MODEL_DICT[remove_key]
    item = model.find(dataparams[remove_key])
    table_name = model.__table__.name
    if item is None:
        msg = "Unable to remove tag; %s #%d does not exist." % (table_name, dataparams[remove_key])
        return set_error(retdata, msg)
    elif tag not in item._tags:
        return set_error(retdata, "Tag '%s' does not exist on %s." % (tag.name, item.shortlink))
    item._tags.remove(tag)
    SESSION.commit()
    return retdata
