# APP/LOGICAL/DATABASE/BASE_DB.PY

# ## PYTHON IMPORTS
import time
import datetime

# ## EXTERNAL IMPORTS
import sqlalchemy
from sqlalchemy import func

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


def set_column_attributes(item, any_columns, null_columns, dataparams,
                          create_attributes=None, update=False, safe=False):
    """For updating column attributes with scalar values"""
    printer = buffered_print('set_column_attributes', safe=True, header=False)
    printer("(%s)" % item.shortlink)
    is_dirty = False
    allowed_attrs = any_columns + null_columns
    create = item not in SESSION
    if create:
        allowed_attrs += create_attributes if create_attributes is not None else []
    for attr in allowed_attrs:
        if attr not in dataparams or (attr in null_columns and getattr(item, attr) is not None):
            continue
        if getattr(item, attr) != dataparams[attr]:
            to_val = _normalize_val(dataparams[attr])
            if create:
                printer("[%s]:" % _get_attr(attr), to_val)
            else:
                from_val = _normalize_val(getattr(item, attr))
                printer("[%s]:" % _get_attr(attr), from_val, '->', to_val)
            setattr(item, attr, dataparams[attr])
            is_dirty = True
    if create:
        if 'created' not in dataparams and hasattr(item, 'created'):
            item.created = get_current_time()
        add_record(item)
    if is_dirty or create:
        if 'updated' not in dataparams:
            _update_record(item, update)
        flush_session(safe=safe)
        printer.print()
    return is_dirty


def set_relationship_collections(item, relationships, dataparams, update=False, safe=False):
    """For updating multiple values to collection relationships with scalar values"""
    printer = buffered_print('set_relationship_collections', safe=True, header=False)
    printer("(%s)" % item.shortlink)
    is_dirty = False
    for collectionname in relationships:
        if dataparams.get(collectionname) is None:
            continue
        collection = getattr(item, collectionname)
        relationship = getattr(item.model, collectionname).target_collection
        current_values = set(collection)
        update_values = set(dataparams[collectionname])
        add_values = update_values - current_values
        for value in add_values:
            printer("+[%s]:" % relationship, _normalize_val(value))
            collection.append(value)
            is_dirty = True
        remove_values = current_values - update_values
        for value in remove_values:
            printer("-[%s]:" % relationship, _normalize_val(value))
            collection.remove(value)
            is_dirty = True
    if is_dirty:
        _update_record(item, update)
        flush_session(safe=safe)
        printer.print()
    return is_dirty


def set_version_relations(item, relationships, dataparams, update=False, safe=False):
    """For assigning a value to a relation and the current value if it exists to a version collection"""
    printer = buffered_print('set_version_relations', safe=True, header=False)
    printer("(%s)" % item.shortlink)
    is_dirty = False
    for relname, collname in relationships:
        if relname not in dataparams:
            continue
        new_value = dataparams.get(relname)
        old_value = getattr(item, relname)
        if new_value == old_value:
            continue
        setattr(item, relname, new_value)
        collection = getattr(item, collname)
        if new_value is not None and new_value in collection:
            collection.remove(new_value)
        if old_value is not None and old_value not in collection:
            collection.append(old_value)
        if old_value is None:
            printer("[%s]:" % _get_attr(relname), _normalize_val(new_value))
        else:
            printer("[%s]:" % _get_attr(relname), _normalize_val(old_value), '->', _normalize_val(new_value))
        is_dirty = True
    if is_dirty:
        _update_record(item, update)
        flush_session(safe=safe)
        printer.print()
    return is_dirty


def save_record(record, action, commit=True, safe=False):
    print("[%s]: %s\n" % (record.shortlink, action))
    # Commit only after printing to avoid unnecessarily requerying the record
    commit_or_flush(commit, safe=safe)


def add_record(record):
    SESSION.add(record)


def delete_record(record):
    SESSION.delete(record)


def commit_session(safe=False):
    if safe:
        safe_commit_session()
    else:
        SESSION.commit()


def flush_session(safe=False):
    if safe:
        safe_flush_session()
    else:
        SESSION.flush()


def commit_or_flush(commit, safe=False):
    if safe:
        safe_commit_or_flush(commit)
    else:
        _commit_or_flush(commit)


def safe_commit_session():
    try:
        SESSION.commit()
    except Exception as e:
        safe_print("\asafe_commit_session : %s" % str(e))
        print("Unlocking the database...")
        SESSION.rollback()
        log_error('base_db.safe_commit_session', str(e))
        _handle_db_exception(e)
        raise


def safe_flush_session():
    try:
        SESSION.flush()
    except Exception as e:
        safe_print("\asafe_flush_session : %s" % str(e))
        print("Unlocking the database...")
        SESSION.rollback()
        log_error('base_db.safe_flush_session', str(e))
        _handle_db_exception(e)
        raise


def safe_commit_or_flush(commit):
    try:
        _commit_or_flush(commit)
    except Exception as e:
        safe_print("\asafe_db_commit : %s" % str(e))
        print("Unlocking the database...")
        SESSION.rollback()
        log_error('base_db.safe_commit_or_flush', str(e))
        _handle_db_exception(e)
        raise


def session_query(q):
    return SESSION.query(q)


def will_update_record(record, data, columns):
    for key in data:
        if key not in columns:
            continue
        if getattr(record, key) != data[key]:
            return True
    return False


def remove_duplicate_items(check_model, check_column, foreign_keys):
    duplicates = check_model.query.group_by(check_column)\
                            .having(func.count(check_column) > 1)\
                            .with_entities(check_column)\
                            .all()
    total = len(duplicates)
    if total == 0:
        return total
    for duplicate in duplicates:
        dup_items = check_model.query.filter(check_column == duplicate[0]).all()
        update_id = dup_items[0].id
        # Remove duplicates in M2M before updating, otherwise it could violate the unique constraint
        for foreign_key in foreign_keys:
            if not foreign_key[0]._secondary_table:
                continue
            attach_model, attach_column, primary_id = foreign_key
            attach_id = attach_column.name
            primary_column = getattr(attach_model, primary_id)
            m2m_items = attach_model.query.filter(attach_column.in_(item.id for item in dup_items)).all()
            seen_primary_ids = set()
            for item in m2m_items:
                if item[primary_id] in seen_primary_ids:
                    attach_model.query.filter(primary_column == item[primary_id],
                                              attach_column == item[attach_id])\
                                      .delete()
                    flush_session()
                else:
                    seen_primary_ids.add(item[primary_id])
        # Update tables to the first item found
        for foreign_key in foreign_keys:
            attach_model, attach_column, *_ = foreign_key
            for item in dup_items[1:]:
                attach_model.query.filter(attach_column == item.id).update({attach_column.name: update_id})
                flush_session()
                delete_record(item)
                flush_session()
    commit_session()
    return total


def prune_unused_items(model, union_clause):
    delete_count = model.query.filter(model.id.not_in(union_clause))\
                              .delete(synchronize_session=False)
    commit_session()
    return delete_count


# #### Private functions

def _handle_db_exception(error):
    if isinstance(error, sqlalchemy.exc.OperationalError) and error.code == 'e3q8':
        print("!!!Sleeping for DB lock!!!")
        time.sleep(30)


def _commit_or_flush(commit):
    if commit:
        SESSION.commit()
    else:
        SESSION.flush()


def _update_record(item, update):
    if update and hasattr(item, 'updated'):
        item.updated = get_current_time()


def _normalize_val(val):
    if isinstance(val, str):
        return repr(val[:60] + '...') if len(val) > 60 else repr(val)
    if isinstance(val, dict):
        return '<dict>'
    if isinstance(val, list):
        return '<list>'
    return val


def _get_attr(attr):
    if attr.endswith('_name') or attr.endswith('_body'):
        return attr[:-5]
    if attr.endswith('_value'):
        return attr[:-6]
    return attr
