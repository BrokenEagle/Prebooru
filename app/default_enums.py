# APP/DEFAULT_ENUMS.PY

# ## LOCAL IMPORTS
from utility.obj import AttrEnum


# ## CLASSES

# #### Column enums

class SiteDescriptorEnum(AttrEnum):
    custom = 0
    pixiv = 1
    pximg = 2
    twitter = 3
    twimg = 4
    twvideo = 5


class ApiDataTypeEnum(AttrEnum):
    illust = 1
    artist = 2
    profile = 3
    page = 4


class ArchiveTypeEnum(AttrEnum):
    post = 1
    illust = 2
    artist = 3
    booru = 4


class PostTypeEnum(AttrEnum):
    user = 1
    subscription = 2


class SubscriptionStatusEnum(AttrEnum):
    idle = 1
    manual = 2
    automatic = 3
    error = 4


class SubscriptionElementStatusEnum(AttrEnum):
    active = 1
    unlinked = 2
    deleted = 3
    archived = 4
    error = 5
    duplicate = 6


class SubscriptionElementKeepEnum(AttrEnum):
    yes = 1
    no = 2
    maybe = 3
    archive = 4


class UploadStatusEnum(AttrEnum):
    complete = 1
    pending = 2
    processing = 3
    duplicate = 4
    error = 5


class UploadElementStatusEnum(AttrEnum):
    unknown = -1
    complete = 0
    duplicate = 1
    pending = 2
    error = 3


# ## Polymorphic enums

class PoolElementTypeEnum(AttrEnum):
    pool_element = -1
    pool_post = 0
    pool_illust = 1
    pool_notation = 2


class SiteDataTypeEnum(AttrEnum):
    site_data = -1
    pixiv_data = 0
    twitter_data = 1


class TagTypeEnum(AttrEnum):
    tag = -1
    site_tag = 0
    user_tag = 1
