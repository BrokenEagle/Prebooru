# APP/LOGICAL/SOURCES/__INIT__.PY

"""For all logic with specific external network sources."""

# ## COLLATION IMPORTS
from . import pixiv_src
from . import twitter_src
from .base_src import NoSource


# ## GLOBAL VARIABLES

SOURCES = [pixiv_src, twitter_src]
SOURCEDICT = {
    'custom': NoSource,
    'pixiv': pixiv_src,
    'pximg': pixiv_src,
    'twitter': twitter_src,
    'twimg': twitter_src,
    'twvideo': twitter_src,
}
