# APP/LOGICAL/RECORDS/BASE_REC.PY

# ## PACKAGE IMPORTS
from utility.uprint import print_error

# ## LOCAL IMPORTS
from ... import SESSION
from ..utility import set_error


# ## FUNCTIONS

def delete_data(record, delete_func, retdata):
    try:
        delete_func(record)
    except Exception as e:
        """Errors must be reported so that the deletion process can be reversed if needed."""
        SESSION.rollback()
        msg = f"Error deleting data [{record.shortlink}]: {repr(e)}"
        print_error(msg)
        return set_error(retdata, msg)
    return retdata
