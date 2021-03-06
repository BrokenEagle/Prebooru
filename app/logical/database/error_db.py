# APP/LOGICAL/DATABASE/ERROR_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Error
from .base_db import update_column_attributes


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
    update_column_attributes(error, update_columns, createparams)
    print("[%s]: created" % error.shortlink)
    return error


def create_error_from_raw_parameters(createparams):
    error = Error()
    update_columns = set(createparams.keys()).intersection(Error.archive_columns)
    update_column_attributes(error, update_columns, createparams)
    print("[%s]: created" % error.shortlink)
    return error


# #### Misc functions

# ###### Create

def create_error(module_name, message):
    return create_error_from_parameters({'module': module_name, 'message': message})


def create_and_append_error(module_name, message, instance):
    error = create_error(module_name, message)
    append_error(instance, error)
    return error


# ###### Add relationship

def extend_errors(instance, errors):
    instance.errors.extend(errors)
    SESSION.commit()


def append_error(instance, error):
    instance.errors.append(error)
    SESSION.commit()


# ###### Test

def is_error(instance):
    return isinstance(instance, Error)
