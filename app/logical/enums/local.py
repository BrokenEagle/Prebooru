# APP/LOGICAL/ENUMS/LOCAL.PY

# ## PACKAGE IMPORTS
from utility.obj import AttrEnum

# ## LOCAL IMPORTS
from .. import sites


# ## CLASSES

# #### Rendered enums

class ApiDataTypeEnum(AttrEnum):
    illust = 0
    artist = 1
    page = 2
    profile = 3
    unknown = 127


class ArchiveTypeEnum(AttrEnum):
    post = 0
    illust = 1
    artist = 2
    booru = 3
    unknown = 127


class PostTypeEnum(AttrEnum):
    subscription = 0
    user = 1
    unknown = 127


class SubscriptionStatusEnum(AttrEnum):
    idle = 0
    retired = 1
    automatic = 2
    manual = 3
    error = 126
    unknown = 127


class SubscriptionElementStatusEnum(AttrEnum):
    active = 0
    deleted = 1
    unlinked = 2
    duplicate = 3
    archived = 5
    error = 126
    unknown = 127


class SubscriptionElementKeepEnum(AttrEnum):
    no = 0
    yes = 1
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
    pending = 1
    duplicate = 4
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
    twimg = 0
    twitter = 1
    twvideo = 2
    pximg = 3
    pixiv = 4
    custom = 126
    unknown = 127

    # ## Instance properties

    source = sites.source
    domain = sites.domain

    # ## Class properties

    get_site_from_domain = sites.get_site_from_domain
    get_site_from_url = sites.get_site_from_url
    get_site_from_id = sites.get_site_from_id
