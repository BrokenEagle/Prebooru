# APP/LOGICAL/DATABASE/BASE_DB.PY

# ## PYTHON IMPORTS
import datetime

# ## LOCAL IMPORTS
from ... import SESSION
from ..utility import process_utc_timestring, safe_print


# ##GLOBAL VARIABLES

def set_timesvalue(params, key):
    if key in params:
        if type(params[key]) is str:
            params[key] = process_utc_timestring(params[key])
        elif type(params[key]) is not datetime.datetime:
            params[key] = None


def update_column_attributes(item, attrs, dataparams):
    """For updating column attributes with scalar values"""
    is_dirty = False
    for attr in attrs:
        if getattr(item, attr) != dataparams[attr]:
            safe_print("Setting basic attr (%s):" % item.shortlink, attr, getattr(item, attr), dataparams[attr])
            setattr(item, attr, dataparams[attr])
            is_dirty = True
    if item.id is None:
        SESSION.add(item)
    if is_dirty:
        SESSION.commit()
    return is_dirty


def update_relationship_collections(item, relationships, updateparams):
    """For updating multiple values to collection relationships with scalar values"""
    is_dirty = False
    for attr, subattr, model in relationships:
        if updateparams[attr] is None:
            continue
        collection = getattr(item, attr)
        current_values = [getattr(subitem, subattr) for subitem in collection]
        add_values = set(updateparams[attr]).difference(current_values)
        for value in add_values:
            safe_print("Adding collection item (%s):" % item.shortlink, attr, value)
            add_item = model.query.filter_by(**{subattr: value}).first()
            if add_item is None:
                add_item = model(**{subattr: value})
                SESSION.add(add_item)
            collection.append(add_item)
            is_dirty = True
        remove_values = set(current_values).difference(updateparams[attr])
        for value in remove_values:
            safe_print("Removing collection item (%s):" % item.shortlink, attr, value)
            remove_item = next(filter(lambda x: getattr(x, subattr) == value, collection))
            collection.remove(remove_item)
            is_dirty = True
    if is_dirty:
        SESSION.commit()
    return is_dirty


def append_relationship_collections(item, relationships, updateparams):
    """For appending a single value to collection relationships with scalar values"""
    is_dirty = False
    for attr, subattr, model in relationships:
        if updateparams[attr] is None:
            continue
        collection = getattr(item, attr)
        current_values = [getattr(subitem, subattr) for subitem in collection]
        if updateparams[attr] not in current_values:
            value = updateparams[attr]
            safe_print("Adding collection item (%s):" % item.shortlink, attr, value)
            add_item = model.query.filter_by(**{subattr: value}).first()
            if add_item is None:
                add_item = model(**{subattr: value})
                SESSION.add(add_item)
            collection.append(add_item)
            is_dirty = True
    if is_dirty:
        SESSION.commit()
    return is_dirty
