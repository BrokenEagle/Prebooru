# APP/LOGICAL/ENUMS/DEFAULT.PY

# ## PACKAGE IMPORTS
from utility.obj import AttrEnum

# ## LOCAL IMPORTS
from .. import sites


# ## CLASSES

# #### Rendered enums

class ApiDataTypeEnum(AttrEnum):
    illust = 0
    artist = 1
    profile = 2
    page = 3
    unknown = 127


class ArchiveTypeEnum(AttrEnum):
    post = 0
    illust = 1
    artist = 2
    booru = 3
    unknown = 127


class PostTypeEnum(AttrEnum):
    user = 0
    subscription = 1
    unknown = 127


class SubscriptionStatusEnum(AttrEnum):
    idle = 0
    retired = 1
    automatic = 2
    manual = 3
    error = 126
    unknown = 127


class SubscriptionElementStatusEnum(AttrEnum):
    unlinked = 0
    deleted = 1
    active = 2
    archived = 3
    duplicate = 4
    error = 126
    unknown = 127


class SubscriptionElementKeepEnum(AttrEnum):
    yes = 0
    no = 1
    maybe = 2
    archive = 3
    unknown = 127


class UploadStatusEnum(AttrEnum):
    complete = 0
    duplicate = 1
    pending = 2
    processing = 3
    error = 126
    unknown = 127


class UploadElementStatusEnum(AttrEnum):
    complete = 0
    duplicate = 1
    pending = 2
    error = 126
    unknown = 127


class PoolElementTypeEnum(AttrEnum):
    pool_post = 0
    pool_illust = 1
    pool_notation = 2
    pool_element = 126
    unknown = 127


class SiteDataTypeEnum(AttrEnum):
    twitter_data = 0
    pixiv_data = 1
    site_data = 126
    unknown = 127


class TagTypeEnum(AttrEnum):
    site_tag = 0
    user_tag = 1
    tag = 126
    unknown = 127


class SiteDescriptorEnum(AttrEnum):
    pixiv = 0
    pximg = 1
    twitter = 2
    twimg = 3
    twvideo = 4
    custom = 126
    unknown = 127

    # ## Instance properties

    source = sites.source
    domain = sites.domain

    # ## Class properties

    get_site_from_domain = sites.get_site_from_domain
    get_site_from_url = sites.get_site_from_url
    get_site_from_id = sites.get_site_from_id
