# APP/LOGICAL/SITES.PY

# ## PYTHON IMPORTS
import enum

# ## PACKAGE IMPORTS
from utility.obj import AttrEnum


# ## GLOBAL VARIABLES

SITES = {
    'CUSTOM': None,
    'PIXIV': 'www.pixiv.net',
    'PXIMG': 'i.pximg.net',
    'TWITTER': 'twitter.com',
    'TWIMG': 'pbs.twimg.com',
    'TWVIDEO': 'video.twimg.com',
}

DOMAINS = {v: k for k, v in SITES.items()}


# ## CLASSES

class Site(AttrEnum):
    CUSTOM = 0
    PIXIV = enum.auto()
    PXIMG = enum.auto()
    TWITTER = enum.auto()
    TWIMG = enum.auto()
    TWVIDEO = enum.auto()

    @property
    def source(self):
        from .sources import SOURCEDICT
        return SOURCEDICT[self.name]

    @property
    def domain(self):
        return SITES[self.name]


# ## FUNCTIONS

def get_site_id(domain):
    if domain in DOMAINS:
        s = DOMAINS[domain]
        return Site[s].value
    return 0


def get_site_domain(site_id):
    return SITES[Site(site_id).name]


def get_site_key(site_id):
    return Site(site_id).name
