# APP/MODELS/BASE.PY

# ## PYTHON IMPORTS
import enum
import json
import zlib
import datetime
from types import SimpleNamespace

# ## EXTERNAL IMPORTS
from flask import url_for, Markup
from sqlalchemy.dialects.sqlite import DATETIME
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.ext.associationproxy import _AssociationList

# ## PACKAGE IMPORTS
from config import HAS_EXTERNAL_IMAGE_SERVER, IMAGE_PORT

# ## LOCAL IMPORTS
from .. import DB, SESSION, SERVER_INFO


# ## FUNCTIONS

# #### Helper functions

def date_time_or_null(value):
    return value if value is None else datetime.datetime.isoformat(value)


def get_column_for_serialize(obj, column):
    value = getattr(obj, column)
    if isinstance(value, enum.Enum):
        return value.value
    else:
        return value


# #### Network functions

def _external_server_url(urlpath, subtype):
    return 'http://' + SERVER_INFO.addr + ':' + str(IMAGE_PORT) + f'/{subtype}/' + urlpath


def _internal_server_url(urlpath, subtype):
    return url_for('media.send_file', subtype=subtype, path=urlpath)


image_server_url = _external_server_url if HAS_EXTERNAL_IMAGE_SERVER else _internal_server_url


# #### Factory functions

def polymorphic_accessor_factory(collection_type, proxy):

    def getter(obj):
        if not hasattr(obj, proxy.value_attr):
            return
        return getattr(obj, proxy.value_attr)

    def setter(obj, value):
        if not hasattr(obj, proxy.value_attr):
            return
        setattr(obj, proxy.value_attr, value)

    return getter, setter


def relation_property_factory(model_key, table_name, relation_key):

    def _shortlink(obj):
        value = getattr(obj, relation_key)
        return "%s #%d" % (table_name, value) if value is not None else "new %s" % table_name

    def _show_url(obj):
        value = getattr(obj, relation_key)
        return url_for("%s.show_html" % table_name, id=value) if value is not None else None

    def _show_link(obj):
        value = getattr(obj, relation_key)
        shortlink = getattr(obj, model_key + '_shortlink')
        show_url = getattr(obj, model_key + '_show_url')
        return Markup('<a href="%s">%s</a>' % (show_url, shortlink)) if value is not None else None

    return _shortlink, _show_url, _show_link


def classproperty(cached=False):
    def _decorator(function):
        return CacheClassProperty(function, cached)
    return _decorator


def secondarytable(*args):
    table = DB.Table(*args)
    table.rowid = DB.column("rowid")
    table.query = SESSION.query(table)
    return table


# ## CLASSES

class CacheClassProperty:
    """Decorator for a Class property with optional caching.
       Must be used with classproperty if the cached is used.
    """
    def __init__(self, func, cached=False):
        self.func = func
        self.cached = cached

    def __get__(self, owner_self, owner_cls):
        val = self.func(owner_cls)
        if self.cached:
            # Overwrites the class method with the value
            setattr(owner_cls, self.func.__name__, val)
        return val


class StaticProperty:
    """Decorator for a static property.
    """
    def __init__(self, fget=None, fset=None, fdel=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel

    def setter(self, fset):
        self.fset = fset
        return self

    def deleter(self, fdel):
        self.fdel = fdel
        return self

    def __get__(self, instance, owner=None):
        return self.fget()

    def __set__(self, instance, value):
        return self.fset(value)

    def __delete__(self, instance):
        return self.fdel()


class ModelEnum(enum.Enum):
    @classproperty(cached=False)
    def names(cls):
        return [e.name for e in cls]

    @classproperty(cached=False)
    def values(cls):
        return [e.value for e in cls]


class NormalizedDatetime(DATETIME):
    def __init__(self, *args, **kwargs):
        kwargs['truncate_microseconds'] = True
        kwargs['timezone'] = False
        kwargs.pop('storage_format', None)
        kwargs.pop('regexp', None)
        super().__init__(*args, **kwargs)


class IntEnum(DB.TypeDecorator):
    """
    Enables passing in a Python enum and storing the enum's *value* in the database.
    The default would have stored the enum's *name* (ie the string).
    """
    impl = DB.Integer
    cache_ok = True

    def __init__(self, enumtype, nullable=False):
        super(IntEnum, self).__init__()
        self._enumtype = enumtype
        self._enumname = enumtype.__name__
        self._names = [e.name for e in self._enumtype]
        self._values = [e.value for e in self._enumtype]
        self._nullable = nullable

    def process_bind_param(self, value, dialect):
        if value in self._values:
            return value
        if value in self._names:
            return self._enumtype[value].value
        if isinstance(value, self._enumtype):
            return value.value
        if value is None and self._nullable:
            return None
        raise ValueError(f"Illegal value to bind for enum {self._enumname}.")

    def process_result_value(self, value, dialect):
        if value in self._values:
            return self._enumtype(value)
        if value is None and self._nullable:
            return None
        raise ValueError(f"Illegal value in DB found for enum {self._enumname}.")


class CompressedJSON(DB.TypeDecorator):
    """
    Stores JSON data as a compressed BLOB instead of a string representation.
    :NOTE: This will make the individual data values non-queryable by SqlAlchemy.
    """
    impl = DB.BLOB
    cache_ok = True

    def process_bind_param(self, value, dialect):
        string_value = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
        encoded_value = string_value.encode('UTF')
        return zlib.compress(encoded_value)

    def process_result_value(self, value, dialect):
        decompressed_value = zlib.decompress(value)
        decoded_value = decompressed_value.decode('UTF')
        return json.loads(decoded_value)


class JsonModel(DB.Model):
    __abstract__ = True

    @classmethod
    def find(cls, id):
        return cls.query.filter_by(id=id).first()

    @property
    def model_name(self):
        return self._model_name()

    @property
    def shortlink(self):
        return "%s #%d" % (self.model_name, self.id) if self.id is not None else "new %s" % self.model_name

    @property
    def header(self):
        return self.shortlink.replace('_', ' ').title()

    @property
    def show_url(self):
        return url_for(self.model_name + ".show_html", id=self.id)

    @property
    def show_link(self):
        return Markup('<a href="%s">%s</a>' % (self.show_url, self.shortlink))

    @property
    def index_url(self):
        return url_for(self.model_name + ".index_html")

    @property
    def create_url(self):
        return url_for(self.model_name + ".create_html")

    @property
    def update_url(self):
        return url_for(self.model_name + ".update_html", id=self.id)

    @property
    def edit_url(self):
        return url_for(self.model_name + ".edit_html", id=self.id)

    @property
    def delete_url(self):
        return url_for(self.model_name + ".delete_html", id=self.id)

    def column_dict(self):
        return {k: get_column_for_serialize(self, k) for k in self.__table__.c.keys() if hasattr(self, k)}

    def archive_dict(self):
        return {k: get_column_for_serialize(self, k) for k in self.archive_columns if hasattr(self, k)}

    def to_json(self):
        data = {}
        for attr in self.json_attributes:
            value = getattr(self, attr)
            if type(value) is datetime.datetime:
                data[attr] = date_time_or_null(value)
            elif isinstance(value, enum.Enum):
                data[attr] = value.value
            elif type(value) is _AssociationList:
                data[attr] = list(value)
            elif type(value) is InstrumentedList:
                data[attr] = [t.to_json() for t in value]
            elif hasattr(value, 'to_json'):
                data[attr] = value.to_json()
            else:
                data[attr] = value
        return data

    @classmethod
    def relations(cls):
        if not hasattr(cls, '_relation_keys'):
            primary_keys = [key for key in cls.__dict__.keys() if not (key.startswith('_') and key.endswith('_'))]
            setattr(cls, '_relation_keys', [])
            for key in primary_keys:
                attr = getattr(cls, key)
                if not hasattr(attr, 'property'):
                    continue
                if type(attr.property) is RelationshipProperty:
                    cls._relation_keys.append(key)
        return cls._relation_keys

    @classmethod
    def fk_relations(cls):
        relations = []
        for key in cls.relations():
            table = cls.__table__
            relation = getattr(cls, key)
            if relation.property.primaryjoin.right.table == table:
                relations.append(key)
        return relations

    @classmethod
    def set_relation_properties(cls):
        for key in cls.fk_relations():
            table_name = getattr(cls, key).property.primaryjoin.left.table.name
            relation_key = getattr(cls, key).property.primaryjoin.right.name
            _shortlink, _show_url, _show_link = relation_property_factory(key, table_name, relation_key)
            setattr(cls, key + '_shortlink', property(_shortlink))
            setattr(cls, key + '_show_url', property(_show_url))
            setattr(cls, key + '_show_link', property(_show_link))

    @classproperty(cached=False)
    def columns(cls):
        return cls.__table__.c

    @classproperty(cached=True)
    def all_columns(cls):
        return cls.columns.keys()

    @classproperty(cached=True)
    def base_columns(cls):
        return [k for k in cls.all_columns if len(getattr(cls.columns, k).foreign_keys) == 0]

    @classproperty(cached=True)
    def fk_columns(cls):
        return [k for k in cls.all_columns if len(getattr(cls.columns, k).foreign_keys) > 0]

    @classproperty(cached=True)
    def archive_columns(cls):
        return [k for k in cls.base_columns if k != 'id']

    @classproperty(cached=True)
    def basic_attributes(cls):
        return [attr for attr in cls.all_columns if (attr in dir(cls) and hasattr(getattr(cls, attr), 'property'))]

    @classproperty(cached=True)
    def relation_attributes(cls):
        return [relation.strip('_') for relation in cls.relations()]

    @classproperty(cached=True)
    def searchable_attributes(cls):
        return cls.basic_attributes + cls.relation_attributes

    @classproperty(cached=False)
    def json_attributes(cls):
        return cls.basic_attributes

    @StaticProperty
    def rowid():
        return DB.column("rowid")

    # Private

    def __repr__(self):
        data = {}
        for attr in self.basic_attributes:
            data[attr] = getattr(self, attr)
        return self.model_name.title() + repr(SimpleNamespace(**data))[9:]

    @classmethod
    def _model_name(cls):
        return cls.__table__.name
