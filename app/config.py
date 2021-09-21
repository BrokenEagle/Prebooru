# APP/CONFIG.PY

# flake8: noqa

import os

from .default_config import *

try:
    if not os.environ.get('DEFAULT_CONFIG'):
        from .local_config import *
except ImportError:
    print("Create an 'app\\local_config.py' file to overwrite the default config.\nUseful for placing information that shouldn't be tracked (e.g. passwords)")


# Environment variables

WORKING_DIRECTORY = os.environ.get('WORKING_DIRECTORY', WORKING_DIRECTORY)
DATA_FILEPATH = os.environ.get('DATA_FILEPATH', DATA_FILEPATH)
IMAGE_FILEPATH = os.environ.get('IMAGE_FILEPATH', IMAGE_FILEPATH)
DB_PATH = os.environ.get('DB_PATH', DB_PATH)
JOBS_PATH = os.environ.get('JOBS_PATH', JOBS_PATH)
DANBOORU_USERNAME = os.environ.get('DANBOORU_USERNAME', DANBOORU_USERNAME)
DANBOORU_APIKEY = os.environ.get('DANBOORU_APIKEY', DANBOORU_APIKEY)
PIXIV_PHPSESSID = os.environ.get('PIXIV_PHPSESSID', PIXIV_PHPSESSID)
PREBOORU_PORT = int(os.environ.get('PREBOORU_PORT', PREBOORU_PORT))
IMAGE_PORT = int(os.environ.get('IMAGE_PORT', IMAGE_PORT))
HAS_EXTERNAL_IMAGE_SERVER = bool(os.environ.get('HAS_EXTERNAL_IMAGE_SERVER', HAS_EXTERNAL_IMAGE_SERVER))
DEBUG_MODE = bool(os.environ.get('DEBUG_MODE', DEBUG_MODE))

# Constructed config variables

IMAGE_DIRECTORY = os.path.join(WORKING_DIRECTORY, IMAGE_FILEPATH)
DATA_DIRECTORY = os.path.join(WORKING_DIRECTORY, DATA_FILEPATH)
