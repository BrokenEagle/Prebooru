# APP/LOGICAL/SOURCES/__INIT__.PY

"""For all logic with specific external network sources."""

# ## COLLATION IMPORTS
from . import pixiv
from . import twitter
from .base import NoSource


# ## GLOBAL VARIABLES

SOURCES = [pixiv, twitter]
SOURCEDICT = {
    'custom': NoSource,
    'pixiv': pixiv,
    'pximg': pixiv,
    'twitter': twitter,
    'twimg': twitter,
    'twvideo': twitter,
}
