# APP/DATABASE/BASE_DB.PY

import datetime

from .. import SESSION
from ..logical.utility import ProcessUTCTimestring, SafePrint


# ##GLOBAL VARIABLES

def SetTimesvalue(params, key):
    if key in params:
        if type(params[key]) is str:
            params[key] = ProcessUTCTimestring(params[key])
        elif type(params[key]) is not datetime.datetime:
            params[key] = None


def UpdateColumnAttributes(item, attrs, dataparams):
    SafePrint("UpdateColumnAttributes", item.column_dict(), attrs, dataparams)
    is_dirty = False
    for attr in attrs:
        if getattr(item, attr) != dataparams[attr]:
            SafePrint("Setting basic attr:", attr, getattr(item, attr), dataparams[attr])
            setattr(item, attr, dataparams[attr])
            is_dirty = True
    if item.id is None:
        SESSION.add(item)
    if is_dirty:
        SESSION.commit()
    return is_dirty


def UpdateRelationshipCollections(item, relationships, updateparams):
    """For updating multiple values to collection relationships with scalar values"""
    is_dirty = False
    for attr, subattr, model in relationships:
        if updateparams[attr] is None:
            continue
        collection = getattr(item, attr)
        current_values = [getattr(subitem, subattr) for subitem in collection]
        add_values = set(updateparams[attr]).difference(current_values)
        for value in add_values:
            SafePrint("Adding collection item:", attr, value)
            add_item = model.query.filter_by(**{subattr: value}).first()
            if add_item is None:
                add_item = model(**{subattr: value})
                SESSION.add(add_item)
            collection.append(add_item)
            is_dirty = True
        remove_values = set(current_values).difference(updateparams[attr])
        for value in remove_values:
            SafePrint("Removing collection item:", attr, value)
            remove_item = next(filter(lambda x: getattr(x, subattr) == value, collection))
            collection.remove(remove_item)
            is_dirty = True
    if is_dirty:
        SESSION.commit()
    return is_dirty


def AppendRelationshipCollections(item, relationships, updateparams):
    """For appending a single value to collection relationships with scalar values"""
    is_dirty = False
    for attr, subattr, model in relationships:
        if updateparams[attr] is None:
            continue
        collection = getattr(item, attr)
        current_values = [getattr(subitem, subattr) for subitem in collection]
        if updateparams[attr] not in current_values:
            value = updateparams[attr]
            SafePrint("Adding collection item:", attr, value)
            add_item = model.query.filter_by(**{subattr: value}).first()
            if add_item is None:
                add_item = model(**{subattr: value})
                SESSION.add(add_item)
            collection.append(add_item)
            is_dirty = True
    if is_dirty:
        SESSION.commit()
    return is_dirty
