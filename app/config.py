# APP/CONFIG.PY

# flake8: noqa

# ## PYTHON IMPORTS
import os

# ## LOCAL IMPORTS
from .default_config import *
from .logical.utility import get_environment_variable, eval_bool_string

try:
    if not get_environment_variable('DEFAULT_CONFIG', False):
        from .local_config import *
except ImportError:
    print("Create an 'app\\local_config.py' file to overwrite the default config.\nUseful for placing information that shouldn't be tracked (e.g. passwords)")


# ## GLOBAL VARIABLES

VERSION = '2.3.1'

# #### Environment-settable variables

WORKING_DIRECTORY = get_environment_variable('WORKING_DIRECTORY', WORKING_DIRECTORY)
DATA_FILEPATH = get_environment_variable('DATA_FILEPATH', DATA_FILEPATH)
IMAGE_FILEPATH = get_environment_variable('IMAGE_FILEPATH', IMAGE_FILEPATH)
DB_PATH = get_environment_variable('DB_PATH', DB_PATH)
JOBS_PATH = get_environment_variable('JOBS_PATH', JOBS_PATH)
DANBOORU_USERNAME = get_environment_variable('DANBOORU_USERNAME', DANBOORU_USERNAME)
DANBOORU_APIKEY = get_environment_variable('DANBOORU_APIKEY', DANBOORU_APIKEY)
PIXIV_PHPSESSID = get_environment_variable('PIXIV_PHPSESSID', PIXIV_PHPSESSID)
PREBOORU_PORT = get_environment_variable('PREBOORU_PORT', PREBOORU_PORT, int)
IMAGE_PORT = get_environment_variable('IMAGE_PORT', IMAGE_PORT, int)
HAS_EXTERNAL_IMAGE_SERVER = get_environment_variable('HAS_EXTERNAL_IMAGE_SERVER', HAS_EXTERNAL_IMAGE_SERVER, eval_bool_string)
DEBUG_MODE = get_environment_variable('DEBUG_MODE', DEBUG_MODE, eval_bool_string)

# #### Constructed config variables

IMAGE_DIRECTORY = os.path.join(WORKING_DIRECTORY, IMAGE_FILEPATH)
DATA_DIRECTORY = os.path.join(WORKING_DIRECTORY, DATA_FILEPATH)
