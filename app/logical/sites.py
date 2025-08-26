# APP/LOGICAL/SITES.PY

# ## PACKAGE IMPORTS
from utility.data import merge_dicts

# ## PYTHON IMPORTS
import urllib.parse


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

DOMAINS = merge_dicts({v: k for k, v in SITES.items() if v is not None}, DOMAIN_ALIASES)


# ## FUNCTIONS

def site_name_by_url(url):
    parse = urllib.parse.urlparse(url)
    return DOMAINS.get(parse.netloc) or 'custom'


def site_name_by_domain(domain):
    return DOMAINS.get(domain)


def domain_by_site_name(site_name):
    return SITES.get(site_name)
