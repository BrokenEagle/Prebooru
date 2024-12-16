# APP/LOGICAL/DATABASE/ERROR_DB.PY

# ## LOCAL IMPORTS
from ...models import Error
from .base_db import set_column_attributes, add_record, delete_record, save_record, commit_session, commit_or_flush


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['module', 'message']
NULL_WRITABLE_ATTRIBUTES = []


# ## FUNCTIONS

# #### Create

def create_error_from_parameters(createparams):
    error = Error()
    return set_error_from_parameters(error, createparams, 'created')


def create_error_from_json(data):
    error = Error.loads(data)
    add_record(error)
    save_record(error, 'created')
    return error


def create_error(module_name, message):
    error = create_error_from_parameters({'module': module_name, 'message': message})
    commit_session()
    return error


def create_and_append_error(module_name, message, instance):
    error = create_error_from_parameters({'module': module_name, 'message': message})
    append_error(instance, error)
    return error


# #### Set

def set_error_from_parameters(error, setparams, action):
    if set_column_attributes(error, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(error, action)
    return error


# #### Delete

def delete_error(error):
    delete_record(error)
    commit_session()


# #### Add relationship

def extend_errors(instance, errors):
    for error in errors:
        append_error(instance, error, commit=False)
    commit_session()


def append_error(instance, error, commit=True):
    table_name = instance.table_name
    append_key = table_name + '_id'
    setattr(error, append_key, instance.id)
    commit_or_flush(commit)


# #### Test

def is_error(instance):
    return isinstance(instance, Error)
