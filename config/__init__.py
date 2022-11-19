# CONFIG/__INIT__.PY

# flake8: noqa

# ## PYTHON IMPORTS
import os
import dotenv
import logging

# ## PACKAGE IMPORTS
from utility import get_environment_variable
from utility.data import eval_bool_string

# ## LOCAL IMPORTS
from .default import *

# ## GLOBAL VARIABLES

VERSION = '2.27.2'

# ## INTITIALIZATION

DEBUG_LOG = get_environment_variable('DEBUG_LOG', False, eval_bool_string)

LOGHANDLER = logging.StreamHandler()
LOGHANDLER.setLevel(logging.DEBUG)
LOGHANDLER.setFormatter(logging.Formatter('%(levelname)s{%(name)s} @%(asctime)s,%(msecs)03d: %(message)s', '%H:%M:%S'))

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG_LOG else logging.INFO)
logger.addHandler(LOGHANDLER)

try:
    if not get_environment_variable('DEFAULT_CONFIG', False, eval_bool_string):
        from .local import *
except ImportError:
    logger.warning("Unable to load 'config\\local.py , using default config instead.")

# #### Load .env file into environment variables if set

dotenv_logger = logging.getLogger('dotenv.main')
dotenv_logger.setLevel(logging.INFO)
dotenv_logger.addHandler(logging.StreamHandler())
DOTENV_FILEPATH = get_environment_variable('DOTENV_FILEPATH', DOTENV_FILEPATH)
if DOTENV_FILEPATH is not None:
    dotenv_logger.info("\n[PID %d] Loading DOTENV file: %s" % (os.getpid(), DOTENV_FILEPATH))
    dotenv.load_dotenv(dotenv_path=DOTENV_FILEPATH, override=True, verbose=True)

# #### Environment-settable variables

WORKING_DIRECTORY = get_environment_variable('WORKING_DIRECTORY', WORKING_DIRECTORY)
DATA_FILEPATH = get_environment_variable('DATA_FILEPATH', DATA_FILEPATH)
MEDIA_FILEPATH = get_environment_variable('MEDIA_FILEPATH', MEDIA_FILEPATH)
DB_PATH = get_environment_variable('DB_PATH', DB_PATH)
JOBS_PATH = get_environment_variable('JOBS_PATH', JOBS_PATH)
DANBOORU_USERNAME = get_environment_variable('DANBOORU_USERNAME', DANBOORU_USERNAME)
DANBOORU_APIKEY = get_environment_variable('DANBOORU_APIKEY', DANBOORU_APIKEY)
PIXIV_PHPSESSID = get_environment_variable('PIXIV_PHPSESSID', PIXIV_PHPSESSID)
PREBOORU_PORT = get_environment_variable('PREBOORU_PORT', PREBOORU_PORT, int)
IMAGE_PORT = get_environment_variable('IMAGE_PORT', IMAGE_PORT, int)
HAS_EXTERNAL_IMAGE_SERVER = get_environment_variable('HAS_EXTERNAL_IMAGE_SERVER', HAS_EXTERNAL_IMAGE_SERVER, eval_bool_string)
WATCHDOG_MAX_MEMORY_MB = get_environment_variable('PREBOORU_MAX_MEMORY', WATCHDOG_MAX_MEMORY_MB, int) * (1024 * 1024)
WATCHDOG_POLLING_INTERVAL = get_environment_variable('WATCHDOG_POLLING_INTERVAL', WATCHDOG_POLLING_INTERVAL, int)
MAXIMUM_PAGINATE_LIMIT = get_environment_variable('MAXIMUM_PAGINATE_LIMIT', MAXIMUM_PAGINATE_LIMIT, eval_bool_string)
DEFAULT_PAGINATE_LIMIT = get_environment_variable('DEFAULT_PAGINATE_LIMIT', DEFAULT_PAGINATE_LIMIT, eval_bool_string)
DEBUG_MODE = get_environment_variable('DEBUG_MODE', DEBUG_MODE, eval_bool_string)

# #### Constructed config variables

MEDIA_DIRECTORY = os.path.join(WORKING_DIRECTORY, MEDIA_FILEPATH)
DATA_DIRECTORY = os.path.join(WORKING_DIRECTORY, DATA_FILEPATH)
TEMP_DIRECTORY = os.path.join(WORKING_DIRECTORY, TEMP_FILEPATH)
EXCLUDE_PATTERNS = EXCLUDE_PATTERNS.union({'*fixes*', '*migrations*', '*site-packages*'})
