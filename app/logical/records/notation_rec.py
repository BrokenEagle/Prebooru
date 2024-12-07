# APP/LOGICAL/RECORDS/NOTATION_REC.PY

# ## LOCAL IMPORTS
from ..database.base_db import commit_or_flush, delete_record
from .pool_rec import delete_pool_element


# ## FUNCTIONS

def delete_notation(notation):
    if notation._pool is not None:
        delete_pool_element(notation._pool)
    delete_record(notation)
    commit_or_flush(True)