# APP/LOGICAL/SOURCES/__INIT__.PY

"""For all logic with specific external network sources."""

# ## COLLATION IMPORTS
from . import pixiv
from . import twitter


# ## GLOBAL VARIABLES

SOURCES = [pixiv, twitter]
SOURCEDICT = {
    'PIXIV': pixiv,
    'PXIMG': pixiv,
    'TWITTER': twitter,
    'TWIMG': twitter,
    'TWVIDEO': twitter
}
