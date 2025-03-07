# APP/LOGICAL/DATABASE/ERROR_DB.PY

# ## LOCAL IMPORTS
from ...models import Error
from .base_db import set_column_attributes, delete_record, save_record, commit_session, commit_or_flush, set_timesvalue


# ## GLOBAL VARIABLES

ANY_WRITABLE_ATTRIBUTES = ['module', 'message']
NULL_WRITABLE_ATTRIBUTES = ['post_id', 'created']


# ## FUNCTIONS

# #### Create

def create_error_from_parameters(createparams, commit=True):
    set_timesvalue(createparams, 'created')
    return set_error_from_parameters(Error(), createparams, 'created', commit)


def create_error(module_name, message, commit=True):
    return create_error_from_parameters({'module': module_name, 'message': message}, commit=commit)


def create_and_append_error(instance, module_name, message, commit=True):
    error = create_error(module_name, message, commit=commit)
    append_error(instance, error, commit=commit)
    return error


def create_and_extend_errors(instance, error_list, commit=True):
    for params in error_list:
        create_and_append_error(instance, *params, commit=False)
    commit_or_flush(commit)


# #### Set

def set_error_from_parameters(error, setparams, action, commit):
    if set_column_attributes(error, ANY_WRITABLE_ATTRIBUTES, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(error, action, commit=commit)
    return error


# #### Delete

def delete_error(error):
    print("[%s]: deleted\n" % error.shortlink)
    delete_record(error)
    commit_session()


# #### Add relationship

def append_error(instance, error, commit=True):
    table_name = instance.table_name
    append_key = table_name + '_id'
    setattr(error, append_key, instance.id)
    commit_or_flush(commit)


# #### Test

def is_error(instance):
    return isinstance(instance, Error)
