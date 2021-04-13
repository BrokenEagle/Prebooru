# APP/SITES.PY

# ##PYTHON IMPORTS
from enum import Enum, auto


# ##GLOBAL VARIABLES

SITES = {
    'PIXIV': 'www.pixiv.net',
    'PXIMG': 'i.pximg.net',
    'TWITTER': 'twitter.com',
    'TWIMG': 'pbs.twimg.com',
    'TWVIDEO': 'video.twimg.com',
}

DOMAINS = {v: k for k, v in SITES.items()}


class Site(Enum):
    PIXIV = auto()
    PXIMG = auto()
    TWITTER = auto()
    TWIMG = auto()
    TWVIDEO = auto()


# ##FUNCTIONS


def GetSiteId(domain):
    if domain in DOMAINS:
        s = DOMAINS[domain]
        return Site[s].value
    return 0


def GetSiteDomain(site_id):
    return SITES[Site(site_id).name]


def GetSiteKey(site_id):
    return Site(site_id).name
