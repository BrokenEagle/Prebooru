# APP/MODELS/MODEL_ENUMS.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import inspect

# ## PACKAGE IMPORTS
from utility.data import merge_dicts

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel, EnumMap


# ## CLASSES

class EnumModel(JsonModel):
    __abstract__ = True

    @classmethod
    def load(cls):
        if inspect(DB.engine).has_table(cls.__tablename__):
            cls.load_tables()
        else:
            cls.load_config()

    @classmethod
    def load_config(cls):
        cls.is_empty = True
        default_map = merge_dicts(cls.__initial_mapping__, cls.__mandatory_mapping__)
        cls._load([{'id': v, 'name': k} for (k, v) in default_map.items()])

    @classmethod
    def load_tables(cls):
        items = cls.query.all()
        if len(items) > 0:
            cls.is_empty = False
            cls._load(items)
        else:
            cls.load_config()

    @classmethod
    def to_id(cls, name):
        return cls.mapping.to_id(name)

    @classmethod
    def to_name(cls, id):
        return cls.mapping.to_name(id)

    @classmethod
    def by_id(cls, id):
        return cls.mapping.by_id(id)

    @classmethod
    def by_name(cls, name):
        return cls.mapping.by_name(name)

    @classmethod
    def has_id(cls, id):
        return cls.mapping.has_id(id)

    @classmethod
    def has_name(cls, name):
        return cls.mapping.has_name(name)

    # ## Private

    @classmethod
    def _load(cls, items):
        default_map = merge_dicts(cls.__initial_mapping__, cls.__mandatory_mapping__)
        cls.mapping = EnumMap(items, model_name=cls.__name__, default_map=default_map,
                              mandatory_map=cls.__mandatory_mapping__)
        for name in cls.mapping._name_map:
            setattr(cls, name, cls.by_name(name))


class SiteDescriptor(EnumModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    __initial_mapping__ = {
        'pixiv': 0,
        'pximg': 1,
        'twitter': 2,
        'twimg': 3,
        'twvideo': 4,
        'twvideo_cf': 5,
    }
    __mandatory_mapping__ = {
        'custom': 126,
        'unknown': 127,
    }


class ApiDataType(EnumModel):
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


class ArchiveType(EnumModel):
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


class PostType(EnumModel):
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


class SubscriptionStatus(EnumModel):
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


class SubscriptionElementStatus(EnumModel):
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


class SubscriptionElementKeep(EnumModel):
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


class DownloadStatus(EnumModel):
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


class DownloadElementStatus(EnumModel):
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


class UploadStatus(EnumModel):
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


# #### Polymorphic enums

class PoolElementType(EnumModel):
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
        'pool_element': 126,
        'unknown': 127,
    }


class TagType(EnumModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    __initial_mapping__ = {
        'site_tag': 0,
        'user_tag': 1,
    }
    __mandatory_mapping__ = {
        'tag': 126,
        'unknown': 127,
    }


# ## Initialize

SiteDescriptor.load()
ApiDataType.load()
ArchiveType.load()
PostType.load()
SubscriptionStatus.load()
SubscriptionElementStatus.load()
SubscriptionElementKeep.load()
DownloadStatus.load()
DownloadElementStatus.load()
UploadStatus.load()
PoolElementType.load()
TagType.load()
