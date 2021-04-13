# APP/DEFAULT_CONFIG.PY

# ## DIRECTORY VARIABLES

"""Filepaths need to end with a double backslash ('\\')"""
"""All backslashes ('\') in a filepath need to be double escaped ('\\')"""

WORKING_DIRECTORY = "C:\\Temp\\"
DATA_FILEPATH = "data\\"
IMAGE_FILEPATH = "pictures\\"


# ## DATABASE VARIABLES

# Relative path to the DB file
DB_PATH = r'db\prebooru.db'
CACHE_PATH = r'db\cache.db'
SIMILARITY_PATH = r'db\similarity.db'


# ## NETWORK VARIABLES

DANBOORU_HOSTNAME = 'https://danbooru.donmai.us'

DANBOORU_USERNAME = None
DANBOORU_APIKEY = None

# Log into Pixiv and get this value from the cookie PHPSESSID
PIXIV_PHPSESSID = None

PREBOORU_PORT = 5000
WORKER_PORT = 4000
SIMILARITY_PORT = 3000
IMAGE_PORT = 1234

HAS_EXTERNAL_IMAGE_SERVER = False

# ## OTHER VARIABLES

VERSION = '1.0.0'
DEBUG_MODE = False
