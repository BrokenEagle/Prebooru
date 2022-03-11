# CONFIG/DEFAULT.PY


# ## DIRECTORY VARIABLES

'''WINDOWS'''
"""Filepaths need to end with a double backslash ('\\')"""
"""All backslashes ('\') in a filepath need to be double escaped ('\\')"""

WORKING_DIRECTORY = "C:\\Temp\\"


'''LINUX'''
"""Filepaths need to end with a forwardslash ('/')"""
'''
WORKING_DIRECTORY = "/tmp/"
'''


"""Subdirectory paths should not begin or end with a directory separator ('\' or '/')"""
DATA_FILEPATH = "data"
IMAGE_FILEPATH = "pictures"

"""Path for loading the .env to load environment variables from. Can either be a relative or an absolute path"""
DOTENV_FILEPATH = None

# ## IMAGE VARIABLES
"""Maximum dimensions of width x height for preview and sample size images"""

PREVIEW_DIMENSIONS = (300, 300)
SAMPLE_DIMENSIONS = (1280, 1920)


# ## DATABASE VARIABLES

# Relative path to the DB file
DB_PATH = r'db\prebooru.db'
JOBS_PATH = r'db\jobs.db'


# ## NETWORK VARIABLES

DANBOORU_HOSTNAME = 'https://danbooru.donmai.us'

DANBOORU_USERNAME = None
DANBOORU_APIKEY = None

# Log into Pixiv and get this value from the cookie PHPSESSID
PIXIV_PHPSESSID = None

PREBOORU_PORT = 5000
IMAGE_PORT = 1234

HAS_EXTERNAL_IMAGE_SERVER = False


# ## WATCHDOG VARIABLES

WATCHDOG_MAX_MEMORY_MB = 2048
WATCHDOG_POLLING_INTERVAL = 60

# ## OTHER VARIABLES

DEBUG_MODE = False