# APP/MODELS/ATTR_ENUMS.PY

# ## LOCAL IMPORTS
from .. import DB
from ..logical import sites
from .base import JsonModel


# ## CLASSES

# #### Column enums

class SiteDescriptor(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Instance properties

    source = sites.source
    domain = sites.domain

    # ## Class properties

    get_site_from_domain = sites.get_site_from_domain
    get_site_from_url = sites.get_site_from_url
    get_site_from_id = sites.get_site_from_id

    # ## Private

    __initial_mapping__ = {
        'pixiv': 0,
        'pximg': 1,
        'twitter': 2,
        'twimg': 3,
        'twvideo': 4,
    }
    __mandatory_mapping__ = {
        'custom': 126,
        'unknown': 127,
    }


class ApiDataType(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    __initial_mapping__ = {
        'illust': 0,
        'artist': 1,
        'profile': 2,
        'page': 3,
    }
    __mandatory_mapping__ = {
        'unknown': 127,
    }


class ArchiveType(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    __initial_mapping__ = {
        'post': 0,
        'illust': 1,
        'artist': 2,
        'booru': 3,
    }
    __mandatory_mapping__ = {
        'unknown': 127,
    }


class PostType(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    __initial_mapping__ = {
        'user': 0,
        'subscription': 1,
    }
    __mandatory_mapping__ = {
        'unknown': 127,
    }


class SubscriptionStatus(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    __initial_mapping__ = {
        'idle': 0,
        'retired': 1,
        'automatic': 2,
        'manual': 3,
    }
    __mandatory_mapping__ = {
        'error': 126,
        'unknown': 127,
    }


class SubscriptionElementStatus(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    __initial_mapping__ = {
        'unlinked': 0,
        'deleted': 1,
        'active': 2,
        'archived': 3,
        'duplicate': 4,
    }
    __mandatory_mapping__ = {
        'error': 126,
        'unknown': 127,
    }


class SubscriptionElementKeep(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    __initial_mapping__ = {
        'yes': 0,
        'no': 1,
        'maybe': 2,
        'archive': 3,
    }
    __mandatory_mapping__ = {
        'unknown': 127,
    }


class UploadStatus(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    __initial_mapping__ = {
        'complete': 0,
        'duplicate': 1,
        'pending': 2,
        'processing': 3,
    }
    __mandatory_mapping__ = {
        'error': 126,
        'unknown': 127,
    }


class UploadElementStatus(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    __initial_mapping__ = {
        'complete': 0,
        'duplicate': 1,
        'pending': 2,
    }
    __mandatory_mapping__ = {
        'error': 126,
        'unknown': 127,
    }


# #### Polymorphic enums

class PoolElementType(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    __initial_mapping__ = {
        'pool_post': 0,
        'pool_illust': 1,
        'pool_notation': 2,
    }
    __mandatory_mapping__ = {
        'pool_element': 127,
    }


class SiteDataType(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    __initial_mapping__ = {
        'twitter_data': 0,
        'pixiv_data': 1,
    }
    __mandatory_mapping__ = {
        'site_data': 127,
    }


class TagType(JsonModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    __initial_mapping__ = {
        'site_tag': 0,
        'user_tag': 1,
    }
    __mandatory_mapping__ = {
        'tag': 127,
    }
