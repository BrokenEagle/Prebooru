from . import pixiv_source
from . import twitter_source

SOURCES = [pixiv_source, twitter_source]
SOURCEDICT = {
    'PIXIV': pixiv_source,
    'PXIMG': pixiv_source,
    'TWITTER': twitter_source,
    'TWIMG': twitter_source,
    'TWVIDEO': twitter_source
}
