from . import pixiv
from . import twitter

SOURCES = [pixiv, twitter]
SOURCEDICT = {
    'PIXIV': pixiv,
    'PXIMG': pixiv,
    'TWITTER': twitter,
    'TWIMG': twitter,
    'TWVIDEO': twitter
}
