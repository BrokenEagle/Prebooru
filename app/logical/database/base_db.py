# APP/LOGICAL/DATABASE/BASE_DB.PY

# ## PYTHON IMPORTS
import time
import datetime

# ## EXTERNAL IMPORTS
import sqlalchemy

# ## PACKAGE IMPORTS
from utility.time import process_utc_timestring, get_current_time
from utility.uprint import safe_print, buffered_print

# ## LOCAL IMPORTS
from ... import SESSION
from ..logger import log_error


# ## FUNCTIONS

def safe_db_execute(func_name, module_name, scope_vars=None, **kwargs):
    for name in ['try_func', 'msg_func', 'error_func', 'finally_func', 'printer']:
        if not((name in kwargs) and (callable(kwargs[name]))):
            kwargs[name] = lambda *args: args[-1]
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


def set_column_attributes(item, any_columns, null_columns, dataparams, update=False):
    """For setting column attributes with scalar values"""
    printer = buffered_print('set_column_attributes', safe=True, header=False)
    printer("(%s)" % item.shortlink)
    is_dirty = False
    current_time = None
    allowed_attrs = any_columns + null_columns
    for attr in allowed_attrs:
        if attr not in dataparams:
            continue
        if attr in null_columns and getattr(item, attr) is not None:
            continue
        if getattr(item, attr) != dataparams[attr]:
            from_val = _normalize_val(getattr(item, attr))
            to_val = _normalize_val(dataparams[attr])
            printer("[%s]:" %  _get_attr(item, attr),
                    _get_val(item, attr, from_val), '->', _get_val(item, attr, to_val))
            setattr(item, attr, dataparams[attr])
            is_dirty = True
    if item not in SESSION:
        if hasattr(item, 'created'):
            current_time = get_current_time()
            item.created = current_time
        add_record(item)
    if is_dirty:
        if hasattr(item, 'updated') and (update or getattr(item, 'updated') is None):
            current_time = get_current_time() if current_time is None else current_time
            item.updated = current_time
        printer.print()
    return is_dirty


def set_relationship_collections(item, relationships, dataparams):
    """For updating multiple values to collection relationships with scalar values"""
    printer = buffered_print('set_relationship_collections', safe=True, header=False)
    printer("(%s)" % item.shortlink)
    is_dirty = False
    for attr, subattr, model in relationships:
        if dataparams.get(attr) is None:
            continue
        collection = getattr(item, attr)
        is_dependant = attr in item.dependant_relations()
        current_values = [getattr(subitem, subattr) for subitem in collection]
        add_values = set(dataparams[attr]).difference(current_values)
        for value in add_values:
            printer("[%s]:" % attr, _normalize_val(value))
            add_item = model.query.filter_by(**{subattr: value}).first()
            if add_item is None:
                add_item = model(**{subattr: value})
                add_record(add_item)
            collection.append(add_item)
            is_dirty = True
        remove_values = set(current_values).difference(dataparams[attr])
        for value in remove_values:
            printer("Removing collection item (%s):" % item.shortlink, attr, value)
            remove_item = next(filter(lambda x: getattr(x, subattr) == value, collection))
            if is_dependant:
                delete_record(remove_item)
            else:
                collection.remove(remove_item)
            is_dirty = True
    if is_dirty:
        printer.print()
    return is_dirty


def append_relationship_collections(item, relationships, dataparams):
    """For appending a single value to collection relationships with scalar values"""
    printer = buffered_print('append_relationship_collections', safe=True, header=False)
    printer("(%s)" % item.shortlink)
    is_dirty = False
    for attr, subattr, model in relationships:
        append_attr = attr + '_append'
        if dataparams.get(append_attr) is None:
            continue
        collection = getattr(item, attr)
        current_values = [getattr(subitem, subattr) for subitem in collection]
        if dataparams[append_attr] not in current_values:
            value = dataparams[append_attr]
            printer("[%s]:" % attr, _normalize_val(value))
            add_item = model.query.filter_by(**{subattr: value}).first()
            if add_item is None:
                add_item = model(**{subattr: value})
                add_record(add_item)
            collection.append(add_item)
            is_dirty = True
    if is_dirty:
        printer.print()
    return is_dirty


def record_from_json(model, data):
    record = model.loads(data)
    SESSION.add(record)
    SESSION.flush()
    print(f"[{record.shortlink}]: created")
    return record


def add_record(record):
    SESSION.add(record)


def delete_record(record):
    SESSION.delete(record)


def save_record(record, commit, action, safe=False):
    commit_or_flush(False, safe)
    print("[%s]: %s\n" % (record.shortlink, action))
    # Commit only after printing to avoid unnecessarily requerying the record
    if commit:
        SESSION.commit()


def commit_or_flush(commit, safe=False):
    if safe:
        safe_db_commit(commit)
    elif commit:
        SESSION.commit()
    else:
        SESSION.flush()


def safe_db_commit(commit):
    try:
        if commit:
            SESSION.commit()
        else:
            SESSION.flush()
    except Exception as e:
        safe_print("\asafe_db_commit : %s" % str(e))
        print("Unlocking the database...")
        SESSION.rollback()
        log_error('base_db.safe_db_commit', str(e))
        _handle_db_exception(e)
        raise


# #### Private functions

def _handle_db_exception(error):
    if isinstance(error, sqlalchemy.exc.OperationalError) and error.code == 'e3q8':
        print("!!!Sleeping for DB lock!!!")
        time.sleep(30)


def _normalize_val(val):
    if isinstance(val, str):
        return val[:50] + '...' if len(val) > 50 else val
    if isinstance(val, dict):
        return '<dict>'
    return val


def _get_attr(item, attr):
    if attr.endswith('_id'):
        key = attr[:-3]
        enum = getattr(item, key + '_enum', None)
        if enum is not None:
            return key
    return attr


def _get_val(item, attr, val):
    if isinstance(val, int) and attr.endswith('_id'):
        key = attr[:-3]
        enum = getattr(item, key + '_enum', None)
        if enum is not None:
            return enum.by_id(val).name
    return val
