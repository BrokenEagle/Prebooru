# APP/DATABASE/ERROR_DB.PY

# ##LOCAL IMPORTS
from .. import models, SESSION
from ..logical.utility import GetCurrentTime
from .base_db import UpdateColumnAttributes


# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['module', 'message']

CREATE_ALLOWED_ATTRIBUTES = ['module', 'message']


# ##FUNCTIONS

# #### DB functions

# ###### CREATE

def CreateErrorFromParameters(createparams):
    current_time = GetCurrentTime()
    error = models.Error(created=current_time)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    UpdateColumnAttributes(error, update_columns, createparams)
    return error


# #### Misc functions

# ###### Create

def CreateError(module_name, message):
    return CreateErrorFromParameters({'module': module_name, 'message': message})


def CreateAndAppendError(module_name, message, instance):
    error = CreateError(module_name, message)
    AppendError(instance, error)
    return error


# ###### Add relationship

def ExtendErrors(instance, errors):
    instance.errors.extend(errors)
    SESSION.commit()


def AppendError(instance, error):
    instance.errors.append(error)
    SESSION.commit()


# ###### Test

def IsError(instance):
    return isinstance(instance, models.Error)
