# APP/LOGICAL/DATABASE/BASE_DB.PY

# ## PYTHON IMPORTS
import time
import datetime

# ## EXTERNAL IMPORTS
import sqlalchemy

# ## PACKAGE IMPORTS
from utility.time import process_utc_timestring
from utility.uprint import safe_print, buffered_print

# ## LOCAL IMPORTS
from ... import SESSION
from ..logger import log_error


# ## FUNCTIONS

def safe_db_execute(func_name, module_name, scope_vars=None, **kwargs):
    for func_name in ['try_func', 'msg_func', 'error_func', 'finally_func', 'printer']:
        if not((func_name in kwargs) and (callable(kwargs[func_name]))):
            kwargs[func_name] = lambda *args: args[-1]
    scope_vars = scope_vars or {}
    data = None
    error = None
    try:
        data = kwargs['try_func'](scope_vars)
    except Exception as e:
        try:
            kwargs['printer'](f"\a\n{func_name}: Exception occured in worker!\n", e)
            kwargs['printer']("Unlocking the database...")
            SESSION.rollback()
            msg = kwargs['msg_func'](scope_vars, e)
            log_error(f"{module_name}.{func_name}", msg)
            _handle_db_exception(e)
            kwargs['error_func'](scope_vars, e)
            error = e
        except Exception as e:
            SESSION.rollback()
            log_error(f"{module_name}.{func_name}", f"safe_db_execute - Exception in error block: {repr(e)}")
            _handle_db_exception(e)
    finally:
        try:
            return kwargs['finally_func'](scope_vars, error, data)
        except Exception as e:
            SESSION.rollback()
            log_error(f"{module_name}.{func_name}", f"safe_db_execute - Exception in finally block: : {repr(e)}")


def set_timesvalue(params, key):
    if key in params:
        if type(params[key]) is str:
            params[key] = process_utc_timestring(params[key])
        elif type(params[key]) is not datetime.datetime:
            params[key] = None


def set_association_attributes(params, associations):
    for key in associations:
        if key in params and params[key]:
            association_key = '_' + key
            params[association_key] = params[key]


def update_column_attributes(item, attrs, dataparams, commit=True):
    """For updating column attributes with scalar values"""
    printer = buffered_print('update_column_attributes', safe=True, header=False)
    is_dirty = False
    for attr in attrs:
        if getattr(item, attr) != dataparams[attr]:
            printer("Setting basic attr (%s):" % item.shortlink, attr, getattr(item, attr), dataparams[attr])
            setattr(item, attr, dataparams[attr])
            is_dirty = True
    if item not in SESSION:
        SESSION.add(item)
    if is_dirty:
        printer.print()
        _safe_db_commit(item, 'update_column_attributes', "Error on record create/update", commit=commit)
    return is_dirty


def update_relationship_collections(item, relationships, updateparams, commit=True):
    """For updating multiple values to collection relationships with scalar values"""
    printer = buffered_print('update_relationship_collections', safe=True, header=False)
    is_dirty = False
    for attr, subattr, model in relationships:
        if updateparams[attr] is None:
            continue
        collection = getattr(item, attr)
        current_values = [getattr(subitem, subattr) for subitem in collection]
        add_values = set(updateparams[attr]).difference(current_values)
        for value in add_values:
            printer("Adding collection item (%s):" % item.shortlink, attr, value)
            add_item = model.query.filter_by(**{subattr: value}).first()
            if add_item is None:
                add_item = model(**{subattr: value})
                SESSION.add(add_item)
            collection.append(add_item)
            is_dirty = True
        remove_values = set(current_values).difference(updateparams[attr])
        for value in remove_values:
            printer("Removing collection item (%s):" % item.shortlink, attr, value)
            remove_item = next(filter(lambda x: getattr(x, subattr) == value, collection))
            collection.remove(remove_item)
            is_dirty = True
    if is_dirty:
        printer.print()
        msg = "Error on adding/removing collection values"
        _safe_db_commit(item, 'update_relationship_collections', msg, commit=commit)
    return is_dirty


def append_relationship_collections(item, relationships, updateparams, commit=True):
    """For appending a single value to collection relationships with scalar values"""
    printer = buffered_print('append_relationship_collections', safe=True, header=False)
    is_dirty = False
    for attr, subattr, model in relationships:
        if updateparams[attr] is None:
            continue
        collection = getattr(item, attr)
        current_values = [getattr(subitem, subattr) for subitem in collection]
        if updateparams[attr] not in current_values:
            value = updateparams[attr]
            printer("Adding collection item (%s):" % item.shortlink, attr, value)
            add_item = model.query.filter_by(**{subattr: value}).first()
            if add_item is None:
                add_item = model(**{subattr: value})
                SESSION.add(add_item)
            collection.append(add_item)
            is_dirty = True
    if is_dirty:
        printer.print()
        _safe_db_commit(item, 'append_relationship_collections', "Error on adding collection value", commit=commit)
    return is_dirty


def record_from_json(model, data):
    record = model.loads(data)
    SESSION.add(record)
    SESSION.flush()
    print(f"[{record.shortlink}]: created")
    return record


def will_update_record(record, data, columns):
    for key in data:
        if key not in columns:
            continue
        if getattr(record, key) != data[key]:
            return True
    return False


# #### Private functions

def _safe_db_commit(item, func_name, message, commit=True):
    try:
        if commit:
            SESSION.commit()
        else:
            SESSION.flush()
    except Exception as e:
        error_message = (message + ' : %s\n\t%s') % (e, str(item))
        safe_print("\a%s : %s" % (func_name, error_message))
        print("Unlocking the database...")
        SESSION.rollback()
        log_error(f'database.base_db.{func_name}', error_message)
        _handle_db_exception(e)
        raise


def _handle_db_exception(error):
    if isinstance(error, sqlalchemy.exc.OperationalError) and error.code == 'e3q8':
        print("!!!Sleeping for DB lock!!!")
        time.sleep(30)
