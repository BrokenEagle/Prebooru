# APP/LOGICAL/RECORDS/TAG_REC.PY

# ## LOCAL IMPORTS
from ...models import Post
from ..utility import set_error
from ..database.base_db import commit_session, flush_session

# ## GLOBAL VARIABLES

ID_MODEL_DICT = {
    'post_id': Post,
}


# ## FUNCTIONS

def append_tag_to_item(tag, append_key, dataparams):
    retdata = {'error': False, 'item': tag.to_json()}
    model = ID_MODEL_DICT[append_key]
    id = dataparams[append_key]
    table_name = model.__table__.name
    if isinstance(id, list):
        items = model.query.filter(model.id.in_(id)).all()
        if len(items) == 0:
            return set_error(retdata, "%ss not found." % table_name)
        single = False
    else:
        item = model.find(dataparams[append_key])
        if item is None:
            return set_error(retdata, "%s not found." % table_name)
        items = [item]
        single = True
    for item in items:
        if tag in item._tags:
            if single:
                return set_error(retdata, "Tag '%s' already added to %s." % (tag.name, item.shortlink))
            else:
                continue
        item._tags.append(tag)
    flush_session()
    if single:
        retdata['append'] = item.to_json()
    commit_session()
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
    commit_session()
    retdata['remove'] = item.to_json()
    return retdata
