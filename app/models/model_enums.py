# APP/MODELS/MODEL_ENUMS.PY

# ## PACKAGE IMPORTS
from utility.obj import classproperty

# ## LOCAL IMPORTS
from .. import DB
from ..logical import sites
from .base import JsonModel


# ## CLASSES

class EnumModel(JsonModel):
    __abstract__ = True

    @classproperty(cached=True)
    def names(cls):
        return list(cls.__initial_mapping__.keys()) + list(cls.__mandatory_mapping__.keys())

    @classproperty(cached=True)
    def values(cls):
        return list(cls.__initial_mapping__.keys()) + list(cls.__mandatory_mapping__.keys())

    @classproperty(cached=True)
    def unknown(cls):
        return cls.by_name('unknown')

    @classmethod
    def by_name(cls, name):
        cls._default_or_value()
        return cls._name_items[name]

    @classmethod
    def by_id(cls, id):
        cls._default_or_value()
        return cls._id_items[id]

    # ## Private

    @classmethod
    def _default_or_value(cls):
        if not hasattr(cls, '_name_items'):
            items = cls.query.all()
            if len(items) == 0:
                items = [cls(id=id, name=name) for (name, id) in cls.cls.__mandatory_mapping__.items()] +\
                        [cls(id=id, name=name) for (name, id) in cls.cls.__initial_mapping__.items()]
            else:
                items = [item.copy() for item in items]
            cls._name_items = {item.name: item for item in items}
            cls._id_items = {item.id: item for item in items}

    _enum_model = True



# #### Column enums

class SiteDescriptor(EnumModel):
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

    @classproperty(cached=True)
    def custom(cls):
        return cls.by_name('custom')

    @classproperty(cached=True)
    def pixiv(cls):
        return cls.by_name('pixiv')

    @classproperty(cached=True)
    def pximg(cls):
        return cls.by_name('pximg')

    @classproperty(cached=True)
    def twitter(cls):
        return cls.by_name('twitter')

    @classproperty(cached=True)
    def twimg(cls):
        return cls.by_name('twimg')

    @classproperty(cached=True)
    def twvideo(cls):
        return cls.by_name('twvideo')

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


class ApiDataType(EnumModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    @classproperty(cached=True)
    def illust(cls):
        return cls.by_name('illust')

    @classproperty(cached=True)
    def artist(cls):
        return cls.by_name('artist')

    @classproperty(cached=True)
    def profile(cls):
        return cls.by_name('profile')

    @classproperty(cached=True)
    def page(cls):
        return cls.by_name('page')

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

    # ## Class properties

    @classproperty(cached=True)
    def post(cls):
        return cls.by_name('post')

    @classproperty(cached=True)
    def illust(cls):
        return cls.by_name('illust')

    @classproperty(cached=True)
    def artist(cls):
        return cls.by_name('artist')

    @classproperty(cached=True)
    def booru(cls):
        return cls.by_name('booru')

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

    @classproperty(cached=True)
    def user(cls):
        return cls.by_name('user')

    @classproperty(cached=True)
    def subscription(cls):
        return cls.by_name('subscription')

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

    @classproperty(cached=True)
    def error(cls):
        return cls.by_name('error')

    @classproperty(cached=True)
    def idle(cls):
        return cls.by_name('idle')

    @classproperty(cached=True)
    def retired(cls):
        return cls.by_name('retired')

    @classproperty(cached=True)
    def automatic(cls):
        return cls.by_name('automatic')

    @classproperty(cached=True)
    def manual(cls):
        return cls.by_name('manual')

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

    @classproperty(cached=True)
    def error(cls):
        return cls.by_name('error')

    @classproperty(cached=True)
    def unlinked(cls):
        return cls.by_name('unlinked')

    @classproperty(cached=True)
    def deleted(cls):
        return cls.by_name('deleted')

    @classproperty(cached=True)
    def active(cls):
        return cls.by_name('active')

    @classproperty(cached=True)
    def archived(cls):
        return cls.by_name('archived')

    @classproperty(cached=True)
    def duplicate(cls):
        return cls.by_name('duplicate')

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

    @classproperty(cached=True)
    def yes(cls):
        return cls.by_name('yes')

    @classproperty(cached=True)
    def no(cls):
        return cls.by_name('no')

    @classproperty(cached=True)
    def maybe(cls):
        return cls.by_name('maybe')

    @classproperty(cached=True)
    def archive(cls):
        return cls.by_name('archive')

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


class UploadStatus(EnumModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    @classproperty(cached=True)
    def error(cls):
        return cls.by_name('error')

    @classproperty(cached=True)
    def complete(cls):
        return cls.by_name('complete')

    @classproperty(cached=True)
    def duplicate(cls):
        return cls.by_name('duplicate')

    @classproperty(cached=True)
    def pending(cls):
        return cls.by_name('pending')

    @classproperty(cached=True)
    def processing(cls):
        return cls.by_name('processing')

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


class UploadElementStatus(EnumModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    @classproperty(cached=True)
    def error(cls):
        return cls.by_name('error')

    @classproperty(cached=True)
    def complete(cls):
        return cls.by_name('complete')

    @classproperty(cached=True)
    def duplicate(cls):
        return cls.by_name('duplicate')

    @classproperty(cached=True)
    def pending(cls):
        return cls.by_name('pending')

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

class PoolElementType(EnumModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    @classproperty(cached=True)
    def pool_element(cls):
        return cls.by_name('pool_element')

    @classproperty(cached=True)
    def pool_post(cls):
        return cls.by_name('pool_post')

    @classproperty(cached=True)
    def pool_illust(cls):
        return cls.by_name('pool_illust')

    @classproperty(cached=True)
    def pool_notation(cls):
        return cls.by_name('pool_notation')

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


class SiteDataType(EnumModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    @classproperty(cached=True)
    def site_data(cls):
        return cls.by_name('site_data')

    @classproperty(cached=True)
    def twitter_data(cls):
        return cls.by_name('twitter_data')

    @classproperty(cached=True)
    def pixiv_data(cls):
        return cls.by_name('pixiv_data')

    # ## Private

    __initial_mapping__ = {
        'twitter_data': 0,
        'pixiv_data': 1,
    }
    __mandatory_mapping__ = {
        'site_data': 126,
        'unknown': 127,
    }


class TagType(EnumModel):
    # ## Columns
    id = DB.Column(DB.INTEGER, primary_key=True)
    name = DB.Column(DB.TEXT, nullable=False)

    # ## Private

    @classproperty(cached=True)
    def tag(cls):
        return cls.by_name('tag')

    @classproperty(cached=True)
    def site_tag(cls):
        return cls.by_name('site_tag')

    @classproperty(cached=True)
    def user_tag(cls):
        return cls.by_name('user_tag')

    # ## Private

    __initial_mapping__ = {
        'site_tag': 0,
        'user_tag': 1,
    }
    __mandatory_mapping__ = {
        'tag': 126,
        'unknown': 127,
    }
