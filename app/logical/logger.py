# APP/LOGICAL/LOGGER.PY

# ##PYTHON IMPORTS
import os
import sys
import time
import traceback

# ###LOCAL IMPORTS
from ..config import DATA_DIRECTORY
from .file import load_default, put_get_json


# ##GLOBAL VARIABLES

ERROR_LOG_FILE = os.path.join(DATA_DIRECTORY, 'error_log.json')


# ##FUNCTIONS

def log_error(module, message):
    all_errors = load_default(ERROR_LOG_FILE, [])
    exc_type, exc_value, exc_tb = sys.exc_info()
    error = traceback.format_exception(exc_type, exc_value, exc_tb)
    all_errors.append({
        'module': module,
        'message': message,
        'traceback': error,
        'time': time.ctime(),
    })
    put_get_json(ERROR_LOG_FILE, 'w', all_errors)
