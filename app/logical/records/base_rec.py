# APP/LOGICAL/RECORDS/BASE_REC.PY

# ## PACKAGE IMPORTS
from utility.uprint import print_error

# ## LOCAL IMPORTS
from ... import SESSION
from ..utility import set_error
from ..database.base_db import commit_session


# ## FUNCTIONS

def delete_data(record, delete_func):
    try:
        delete_func(record)
    except Exception as e:
        """Errors must be reported so that the deletion process can be reversed if needed."""
        SESSION.rollback()
        msg = f"Error deleting data [{record.shortlink}]: {repr(e)}"
        print_error(msg)
        return {'error': True, 'message': msg}
    return {'error': False}


def delete_version_relation(item, attach_model, m2m_model, attach_id, item_col, attach_col, display):
    retdata = _relation_params_check(item, attach_model, m2m_model, attach_id, item_col, attach_col, display)
    if retdata['error']:
        return retdata
    m2m_model.query.filter_by(**{item_col: item.id, attach_col: attach_id}).delete()
    commit_session()
    return retdata


def swap_version_relation(item, attach_model, m2m_model, attach_id, item_col, attach_col, relname, collname, display):
    retdata = _relation_params_check(item, attach_model, m2m_model, attach_id, item_col, attach_col, display)
    if retdata['error']:
        return retdata
    m2m_model.query.filter_by(**{item_col: item.id, attach_col: attach_id}).delete()
    swap = getattr(item, relname)
    setattr(item, relname, retdata['attach'])
    if swap is not None:
        getattr(item, collname).append(swap)
    commit_session()
    return retdata


# ## Private

def _relation_params_check(item, attach_model, m2m_model, attach_id, item_col, attach_col, display):
    retdata = {'error': False}
    attach = attach_model.find(attach_id)
    if attach is None:
        return set_error(retdata, "%s #%d does not exist." % (attach_model.model_name, attach_id))
    retdata['attach'] = attach
    m2m_row = m2m_model.query.filter_by(**{item_col: item.id, attach_col: attach_id}).one_or_none()
    if m2m_row is None:
        msg = "%s with %s does not exist on %s." % (display, attach.shortlink, item.shortlink)
        return set_error(retdata, msg)
    return retdata
