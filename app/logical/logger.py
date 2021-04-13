# APP/LOGICAL/LOGGER.PY

# ##PYTHON IMPORTS
import sys
import time
import traceback

# ###LOCAL IMPORTS
from ..config import WORKING_DIRECTORY, DATA_FILEPATH
from .file import LoadDefault, PutGetJSON


# ##GLOBAL VARIABLES

ERROR_LOG_FILE = WORKING_DIRECTORY + DATA_FILEPATH + 'error_log.json'


# ##FUNCTIONS


def LogError(module, message):
    all_errors = LoadDefault(ERROR_LOG_FILE, [])
    exc_type, exc_value, exc_tb = sys.exc_info()
    error = traceback.format_exception(exc_type, exc_value, exc_tb)
    all_errors.append({
        'module': module,
        'message': message,
        'traceback': error,
        'time': time.ctime(),
    })
    PutGetJSON(ERROR_LOG_FILE, 'w', all_errors)
