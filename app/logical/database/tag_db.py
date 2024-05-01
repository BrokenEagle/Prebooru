# APP/LOGICAL/DATABASE/TAG_DB.PY

# ## PACKAGE IMPORTS


# ## LOCAL IMPORTS
from ...models import SiteTag, UserTag, Post
from ..utility import set_error
from .base_db import set_column_attributes, commit_or_flush


# ## GLOBAL VARIABLES

CREATE_ALLOWED_ATTRIBUTES = ['name']

TAG_MODEL_DICT = {
    'site_tag': SiteTag,
    'user_tag': UserTag,
}

ID_MODEL_DICT = {
    'post_id': Post,
}


# ## FUNCTIONS

def create_tag_from_parameters(createparams, commit=True):
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(Tag.all_columns)
    tag = TAG_MODEL_DICT[createparams['type']]()
    set_column_attributes(tag, update_columns, createparams)
    commit_or_flush(commit)
    print("[%s]: created" % tag.shortlink)
    return tag


def append_tag_to_item(tag, append_key, dataparams):
    retdata = {'error': False, 'item': tag.to_json()}
    model = ID_MODEL_DICT[append_key]
    item = model.find(dataparams[append_key])
    table_name = model.__table__.name
    if item is None:
        msg = "Unable to append tag; %s #%d does not exist." % (table_name, dataparams[append_key])
        return set_error(retdata, msg)
    elif tag in item._tags:
        return set_error(retdata, "Tag '%s' already added to %s." % (tag.name, item.shortlink))
    item._tags.append(tag)
    commit_or_flush(True)
    retdata['append'] = item.to_json()
    return retdata


def remove_tag_from_item(tag, remove_key, dataparams):
    retdata = {'error': False, 'item': tag.to_json()}
    model = ID_MODEL_DICT[remove_key]
    item = model.find(dataparams[remove_key])
    table_name = model.__table__.name
    if item is None:
        msg = "Unable to remove tag; %s #%d does not exist." % (table_name, dataparams[remove_key])
        return set_error(retdata, msg)
    elif tag not in item._tags:
        return set_error(retdata, "Tag '%s' does not exist on %s." % (tag.name, item.shortlink))
    item._tags.remove(tag)
    commit_or_flush(True)
    retdata['remove'] = item.to_json()
    return retdata
