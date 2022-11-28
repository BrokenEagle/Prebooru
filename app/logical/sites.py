# APP/LOGICAL/SITES.PY

from .enums import SiteDescriptorEnum


# ## GLOBAL VARIABLES

SITES = {
    'custom': None,
    'pixiv': 'www.pixiv.net',
    'pximg': 'i.pximg.net',
    'twitter': 'twitter.com',
    'twimg': 'pbs.twimg.com',
    'twvideo': 'video.twimg.com',
}

DOMAINS = {v: k for k, v in SITES.items()}


# ## FUNCTIONS

@property
def source(self):
    from .sources import SOURCEDICT
    return SOURCEDICT[self.name]


@property
def domain(self):
    return SITES[self.name]


def get_site_from_domain(domain):
    if domain in DOMAINS:
        s = DOMAINS[domain]
        return SiteDescriptorEnum[s].value
    return 0


def get_site_domain(site):
    return SITES[SiteDescriptorEnum(site).name]


def get_site_key(site):
    return SiteDescriptorEnum(site).name


# ## Initialization

SiteDescriptorEnum.source = source
SiteDescriptorEnum.domain = domain
