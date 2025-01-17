# APP/LOGICAL/SITES.PY

# ## PYTHON IMPORTS
import urllib.parse

# ## PACKAGE IMPORTS
from utility.data import merge_dicts

# ## GLOBAL VARIABLES

SITES = {
    'custom': None,
    'pixiv': 'www.pixiv.net',
    'pximg': 'i.pximg.net',
    'twitter': 'twitter.com',
    'twimg': 'pbs.twimg.com',
    'twvideo': 'video.twimg.com',
    'twvideo_cf': 'video-cf.twimg.com',
}

DOMAIN_ALIASES = {
    'x.com': 'twitter',
}

DOMAINS = merge_dicts({v: k for k, v in SITES.items()}, DOMAIN_ALIASES)


# ## FUNCTIONS

@property
def source(self):
    from .sources import SOURCEDICT
    return SOURCEDICT[self.name]


@property
def domain(self):
    return SITES[self.name]


@classmethod
def get_site_from_domain(cls, domain):
    if domain in DOMAINS:
        s = DOMAINS[domain]
        return getattr(cls, s)
    return getattr(cls, 'custom')


@classmethod
def get_site_from_url(cls, url):
    parse = urllib.parse.urlparse(url)
    return cls.get_site_from_domain(parse.netloc)


@classmethod
def get_site_from_id(cls, id):
    val = cls.find(id)
    if val is not None:
        return val.copy()
    values = cls.values
    if id in values:
        name = cls.names[values.index(id)]
        return cls(id=id, name=name)
