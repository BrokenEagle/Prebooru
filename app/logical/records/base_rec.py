# APP/LOGICAL/RECORDS/BASE_REC.PY

# ## PACKAGE IMPORTS
from utility.uprint import print_error

# ## LOCAL IMPORTS
from ... import SESSION


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
