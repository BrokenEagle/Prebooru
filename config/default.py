# CONFIG/DEFAULT.PY


# ## DIRECTORY VARIABLES

'''WINDOWS'''
"""Filepaths need to end with a double backslash ('\\')"""
"""All backslashes ('\') in a filepath need to be double escaped ('\\')"""

WORKING_DIRECTORY = "C:\\Temp\\"
ALTERNATE_MEDIA_DIRECTORY = None

'''LINUX'''
"""Filepaths need to end with a forwardslash ('/')"""
'''
WORKING_DIRECTORY = "/tmp/"
'''


"""Subdirectory paths should not begin or end with a directory separator ('\' or '/')"""
DATA_FILEPATH = "data"
MEDIA_FILEPATH = "media"
TEMP_FILEPATH = "temp"

"""Path for loading the .env to load environment variables from. Can either be a relative or an absolute path"""
DOTENV_FILEPATH = None

# ## IMAGE VARIABLES
"""Maximum dimensions of width x height for preview and sample size images"""

PREVIEW_DIMENSIONS = (300, 300)
SAMPLE_DIMENSIONS = (1280, 1920)

# ## VIDEO VARIABLES

MP4_SKIP_FRAMES = 5  # How many frames to skip between, e.g. 5 means every 1 in 5 frames will be used
MP4_MIN_FRAMES = 50  # Minimum number of frames before they will be skipped
WEBP_QUALITY = 5  # 0 - 100, higher numbers are better quality, but higher filesizes as well
WEBP_LOOPS = 1

# ## DATABASE VARIABLES

# Relative path to the DB file
DB_PATH = r'db\prebooru.db'
JOBS_PATH = r'db\jobs.db'


NAMING_CONVENTION = {
    "ix": 'ix_%(table_name)s_%(column_0_N_name)s',
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

# ## NETWORK VARIABLES

DANBOORU_HOSTNAME = 'https://danbooru.donmai.us'

DANBOORU_USERNAME = None
DANBOORU_APIKEY = None

# Log into Pixiv and get these values
PIXIV_PHPSESSID = None  # PHPSESSID

# Log into Twitter and get these values
TWITTER_USER_TOKEN = None  # auth_token
TWITTER_CSRF_TOKEN = None  # ct0

PREBOORU_PORT = 5000
IMAGE_PORT = 1234

HAS_EXTERNAL_IMAGE_SERVER = False

# ## TASK VARIABLES
"""Format for task variables is PERIOD {days, hours, minutes}, DURATION, JITTER (seconds), LEEWAY (seconds)."""
EXPUNGE_CACHE_RECORDS = ('hours', 8, 600, 60)
EXPUNGE_ARCHIVE_RECORDS = ('hours', 12, 1200, 180)
GENERATE_MISSING_IMAGE_HASHES = ('days', 2, 3600, 180)
CALCULATE_SIMILARITY_MATCHES = ('days', 1, 3600, 360)
CHECK_ALL_BOORUS = ('days', 1, 3600, 300)
CHECK_ALL_ARTISTS_FOR_BOORUS = ('days', 1, 3600, 300)
CHECK_ALL_POSTS_FOR_DANBOORU_ID = ('days', 1, 3600, 600)
CHECK_PENDING_SUBSCRIPTIONS = ('hours', 1, 300, 180)
CHECK_PENDING_DOWNLOADS = ('hours', 1, 300, 180)
UNLINK_EXPIRED_SUBSCRIPTION_ELEMENTS = ('hours', 8, 600, 300)
DELETE_EXPIRED_SUBSCRIPTION_ELEMENTS = ('hours', 2, 300, 60)
ARCHIVE_EXPIRED_SUBSCRIPTION_ELEMENTS = ('hours', 4, 300, 200)
RECALCULATE_POOL_POSITIONS = ('days', 1, 3600, 600)
RELOCATE_OLD_POSTS = ('hours', 4, 300, 600)
DELETE_ORPHAN_IMAGES = ('weeks', 1, 3600, 300)
VACUUM_ANALYZE_DATABASE = ('weeks', 1, 3600, 60)

# ## SUBSCRIPTION VARIABLES

# #### How many items are processed per batch
POPULATE_ELEMENTS_PER_PAGE = 50
SYNC_MISSING_ILLUSTS_PER_PAGE = 10
DOWNLOAD_POSTS_PER_PAGE = 5
UNLINK_ELEMENTS_PER_PAGE = 50
DELETE_ELEMENTS_PER_PAGE = 10
ARCHIVE_ELEMENTS_PER_PAGE = 10

# #### How many pages to process with automatic tasks
DOWNLOAD_POSTS_PAGE_LIMIT = 20
EXPIRE_ELEMENTS_PAGE_LIMIT = 20  # unlink, delete, archive

"""
Note: The combination of per page and page limit for downloading posts and expiring subscription elements will control
how many items get processed in total, thus controlling roughly how long a task will take when processed automatically.
"""

# ## WATCHDOG VARIABLES

WATCHDOG_MAX_MEMORY_MB = 2048
WATCHDOG_POLLING_INTERVAL = 60

# ## RELOADER VARIABLES

RELOAD_INTERVAL = 60
EXCLUDE_PATTERNS = set()

# ## OTHER VARIABLES

ALTERNATE_MOVE_DAYS = None

MAXIMUM_PAGINATE_LIMIT = 1000
DEFAULT_PAGINATE_LIMIT = 20

MAXIMUM_PROCESS_SUBSCRIPTIONS = 10
SHOW_SUBSCRIPTIONS_WITH_PENDING_ELEMENTS = 10

EXPIRED_SUBSCRIPTION = True

CHECK_FOREIGN_KEYS = False
USE_ENUMS = True

DEBUG_MODE = False
DEBUG_LOG = False
DEBUG_VERBOSE = False
