# APP/LOGICAL/LOGGER.PY

# ## PYTHON IMPORTS
import os
import sys
import time
import traceback

# ## PACKAGE IMPORTS
from config import DATA_DIRECTORY
from utility.file import load_default, put_get_json


# ## GLOBAL VARIABLES

ERROR_LOG_FILE = os.path.join(DATA_DIRECTORY, 'error_log.json')
NETWORK_ERROR_LOG_FILE = os.path.join(DATA_DIRECTORY, 'network_error_log.json')


# ## FUNCTIONS

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


def log_network_error(module, response):
    all_errors = load_default(NETWORK_ERROR_LOG_FILE, [])
    try:
        content = response.json()
    except Exception:
        content = response.text
    all_errors.append({
        'module': module,
        'url': response.url,
        'status_code': response.status_code,
        'reason': response.reason,
        'content': content,
        'time': time.ctime(),
    })
    put_get_json(NETWORK_ERROR_LOG_FILE, 'w', all_errors)
