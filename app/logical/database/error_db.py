# APP/LOGICAL/DATABASE/ERROR_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ...models import Error
from .base_db import update_column_attributes, add_record, delete_record, commit_session, commit_or_flush


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['module', 'message']

CREATE_ALLOWED_ATTRIBUTES = ['module', 'message']


# ## FUNCTIONS

# #### DB functions

# ###### CREATE

def create_error_from_parameters(createparams):
    current_time = get_current_time()
    error = Error(created=current_time)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(error, update_columns, createparams, commit=False)
    print("[%s]: created" % error.shortlink)
    return error


def create_error_from_json(data):
    error = Error.loads(data)
    add_record(error)
    commit_session()
    print("[%s]: created" % error.shortlink)
    return error


# #### Misc functions

# ###### Create

def create_error(module_name, message):
    error = create_error_from_parameters({'module': module_name, 'message': message})
    commit_session()
    return error


def create_and_append_error(module_name, message, instance):
    error = create_error_from_parameters({'module': module_name, 'message': message})
    append_error(instance, error)
    return error


# ###### Delete
def delete_error(error):
    delete_record(error)
    commit_session()


# ###### Add relationship

def extend_errors(instance, errors):
    for error in errors:
        append_error(instance, error, commit=False)
    commit_session()


def append_error(instance, error, commit=True):
    table_name = instance.table_name
    append_key = table_name + '_id'
    setattr(error, append_key, instance.id)
    commit_or_flush(commit)


# ###### Test

def is_error(instance):
    return isinstance(instance, Error)
