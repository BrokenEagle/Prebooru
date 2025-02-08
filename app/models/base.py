# APP/MODELS/BASE.PY

# ## PYTHON IMPORTS
import re
import json
import zlib
import datetime
from types import SimpleNamespace

# ## EXTERNAL IMPORTS
from flask import url_for, Markup
from sqlalchemy import Column, ForeignKey, INTEGER, TEXT, BOOLEAN, BLOB, REAL, JSON
from sqlalchemy.dialects.sqlite import DATETIME
from sqlalchemy.orm import RelationshipProperty, ColumnProperty, relationship, backref
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.ext.associationproxy import _AssociationList

# ## PACKAGE IMPORTS
from config import HAS_EXTERNAL_IMAGE_SERVER, IMAGE_PORT
from utility.time import process_utc_timestring, datetime_from_epoch, datetime_to_epoch, datetime_valid
from utility.obj import classproperty, StaticProperty

# ## LOCAL IMPORTS
from .. import DB, SESSION, SERVER_INFO


# ## GLOBAL VARIABLES

ISODATETIME_RG = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')

sqlalchemy_relationship = relationship
sqlalchemy_backref = backref


# ## FUNCTIONS

# #### JSON functions

def json_serialize(record, attr):
    value = getattr(record, attr)
    if isinstance(value, datetime.datetime):
        value = value.isoformat()
    return value


def json_deserialize(value):
    if isinstance(value, str) and ISODATETIME_RG.match(value):
        value = process_utc_timestring(value)
        if value is None:
            raise Exception("Unable to decode timestring.")
    return value


def validate_attachment_json(values, datatypes):
    if not isinstance(values, list):
        raise ValueError("Base value must be an array.")
    if len(values) == 0:
        return None
    save_values = []
    for item in values:
        if not isinstance(item, dict):
            raise ValueError("Items of array must be a dictionary.")
        save_item = []
        for k in datatypes.keys():
            if k not in item:
                raise ValueError(f"Dictionary missing field: {k}")
            v = item.get(k)
            if not datatypes[k](v):
                raise ValueError(f"Dicionary value invalid type for field: item[{k}] = {v}")
            if k in ('created', 'updated') and not datetime_valid(v):
                raise ValueError(f"Dictionary value must be a valid datetime: item[{k}] = {v}")
            save_item.append(v)
        save_values.append(save_item)
    return save_values


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


def secondarytable(*args, index=False):
    @property
    def _query(self):
        return SESSION.query(self)

    col1_name, col1_fkey = args[1]
    column_1 = Column(col1_name, INTEGER, ForeignKey(col1_fkey), primary_key=True)
    col2_name, col2_fkey = args[2]
    column_2 = Column(col2_name, INTEGER, ForeignKey(col2_fkey), primary_key=True, index=index)
    table = DB.Table(args[0], column_1, column_2, sqlite_with_rowid=False)
    table.__class__.query = _query
    table._model_name = lambda: args[0]
    table._secondary_table = True
    for col in table.columns.keys():
        setattr(table, col, getattr(table.c, col))
    return table


def json_list_proxy(columnname, datatype):

    @property
    def _json_proxy(self):
        value = getattr(self, columnname)
        return value if value is not None else []

    @_json_proxy.setter
    def _json_proxy(self, value):
        if value is None:
            setattr(self, columnname, value)
        elif isinstance(value, list):
            if len(value) > 0:
                for v in value:
                    if not isinstance(v, datatype):
                        raise ValueError(f"Array items must be of type {datatype}")
                setattr(self, columnname, value)
            else:
                setattr(self, columnname, None)
        else:
            raise ValueError("Base value must be an array")

    return _json_proxy


# ## Register

def register_enum_column(model, enum_model, relation):
    id_col = getattr(model, relation + '_id')

    @property
    def enum_relation(self):
        enum_val = getattr(self, relation + '_id')
        return enum_model.mapping.by_id(enum_val)

    @property
    def enum_name(self):
        enum = getattr(self, relation)
        return enum.name if enum is not None else None

    @enum_name.setter
    def enum_name(self, value):
        if value is None:
            set_value = None
        else:
            enum = enum_model.by_name(value)
            if enum is None:
                raise ValueError(f"Invalid value for {relation}")
            set_value = enum.id
        setattr(self, relation + '_id', set_value)

    setattr(model, relation + '_value', EnumColumn(id_col, enum_model.mapping))
    setattr(model, relation + '_enum', enum_model)
    setattr(model, relation + '_name', enum_name)
    setattr(model, relation, enum_relation)


# #### Columns

def base_column(*args, **kwargs):
    if 'foreign_key' in kwargs:
        args = (args[0], ForeignKey(kwargs['foreign_key']), *args[1:])
        del kwargs['foreign_key']
    return Column(*args, **kwargs)


def integer_column(*args, **kwargs):
    return base_column(INTEGER, *args, **kwargs)


def text_column(*args, **kwargs):
    return base_column(TEXT, *args, **kwargs)


def boolean_column(*args, **kwargs):
    return base_column(BOOLEAN, *args, **kwargs)


def blob_column(*args, **kwargs):
    return base_column(BLOB, *args, **kwargs)


def real_column(*args, **kwargs):
    return base_column(REAL, *args, **kwargs)


def json_column(*args, **kwargs):
    return base_column(JSON(none_as_null=True), *args, **kwargs)


def enum_column(*args, **kwargs):
    return base_column(IntEnum, *args, **kwargs)


def timestamp_column(*args, **kwargs):
    return base_column(EpochTimestamp(nullable=kwargs.get('nullable', False)), *args, **kwargs)


def md5_column(*args, **kwargs):
    return base_column(BlobMD5(nullable=kwargs.get('nullable', False)), *args, **kwargs)


def compressed_json_column(*args, **kwargs):
    return base_column(CompressedJSON, *args, **kwargs)


# #### Relationships

def relationship(*args, **kwargs):
    return sqlalchemy_relationship(*args, lazy=True, **kwargs)


def backref(*args, **kwargs):
    return sqlalchemy_backref(*args, lazy=True, **kwargs)


def relation_association_proxy(column_name, relation_name, subattr, creator):
    """The association proxy that comes with sqlalchemy does not handle setting the value ID via a creator."""

    @property
    def value(self):
        relation = getattr(self, relation_name) if getattr(self, column_name) is not None else None
        return getattr(relation, subattr) if relation is not None else None

    @value.setter
    def value(self, value):
        if value is not None:
            item = creator(value)
            setattr(self, column_name, item.id)
        else:
            setattr(self, column_name, value)

    return value


# ## CLASSES

class EnumNamespace(SimpleNamespace):
    def __init__(self, item, model_name=None):
        if isinstance(item, dict):
            super().__init__(**item)
            self._model_name = model_name
        else:
            super().__init__(**item.to_json())
            self._model_name = item.__class__.__name__

    def __repr__(self):
        return f"{self._model_name}(id={self.id}, name={self.name})"


class EnumMap():
    def __init__(self, items, model_name=None, default_map=None, mandatory_map=None):
        self._items = [EnumNamespace(item, model_name=model_name) for item in items]
        self._id_map = {item.id: item for item in self._items}
        self._name_map = {item.name: item for item in self._items}
        self._default_map = default_map
        self._mandatory_map = mandatory_map

    @property
    def needs_upgrade(self):
        return len(set(self._default_map.keys()).symmetric_difference(self._name_map.keys())) > 0

    def to_id(self, name):
        return self.by_name(name).id if self.has_name(name) else None

    def to_name(self, id):
        return self.by_id(id).name if self.has_id(id) else None

    def by_id(self, id):
        return self._id_map[id] if self.has_id(id) else None

    def by_name(self, name):
        return self._name_map[name] if self.has_name(name) else None

    def has_id(self, id):
        return id in self._id_map

    def has_name(self, name):
        return name in self._name_map


class EnumColumn():
    def __init__(self, column, mapper):
        self.column = column
        self.mapper = mapper

    def __ne__(self, value):
        id = self.mapper.to_id(value)
        return self.column != id if id is not None else True

    def __eq__(self, value):
        id = self.mapper.to_id(value)
        return self.column == id if id is not None else True

    def in_(self, values):
        ids = [self.mapper.to_id(v) for v in values]
        ids = [id for id in ids if id is not None]
        return self.column.in_(ids) if len(ids) else True

    def not_in(self, values):
        ids = [self.mapper.to_id(v) for v in values]
        ids = [id for id in ids if id is not None]
        return self.column.not_in(ids) if len(ids) else True

    def is_(self, value):
        return self.column.is_(value) if value is None else True

    def is_not(self, value):
        return self.column.is_not(value) if value is None else True


class NormalizedDatetime(DATETIME):
    def __init__(self, *args, **kwargs):
        kwargs['truncate_microseconds'] = True
        kwargs['timezone'] = False
        kwargs.pop('storage_format', None)
        kwargs.pop('regexp', None)
        super().__init__(*args, **kwargs)


class EpochTimestamp(DB.TypeDecorator):
    impl = DB.Integer
    cache_ok = True

    def __init__(self, nullable=False):
        super(EpochTimestamp, self).__init__()
        self._nullable = nullable

    def process_bind_param(self, value, dialect):
        if isinstance(value, float):
            value = int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            value = process_utc_timestring(value)
        if isinstance(value, datetime.datetime):
            return int(datetime_to_epoch(value))
        if value is None and self._nullable:
            return None
        raise ValueError(f"Illegal value to bind for timestamp: {value}")

    def process_result_value(self, value, dialect):
        if isinstance(value, int):
            return datetime_from_epoch(value)
        if value is None and self._nullable:
            return None
        raise ValueError(f"Illegal value in DB found for timestamp: {value}")


class BlobMD5(DB.TypeDecorator):
    impl = DB.BLOB
    cache_ok = True

    def __init__(self, nullable=False):
        super(BlobMD5, self).__init__()
        self._nullable = nullable

    def process_bind_param(self, value, dialect):
        if isinstance(value, bytes):
            return value
        if isinstance(value, str):
            match = re.match(r'(?:0x)?([0-9a-f]{32})', value, re.IGNORECASE)
            if match:
                return bytes.fromhex(match.group(1))
        if isinstance(value, int):
            return value.to_bytes(16, 'big')
        if value is None and self._nullable:
            return None
        raise ValueError(f"Illegal value to bind for MD5: {value}")

    def process_result_value(self, value, dialect):
        if isinstance(value, bytes):
            return value.hex()
        if value is None and self._nullable:
            return None
        raise ValueError(f"Illegal value in DB found for MD5: {value}")


class IntEnum(DB.TypeDecorator):
    """Column class for enums that can be detected outside of the model definition."""
    impl = DB.Integer
    cache_ok = True


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
    def find(cls, *args, **kwargs):
        if len(args):
            kwargs = {cls.primary_keys[i]: args[i] for i in range(len(args))}
        return cls.query.filter_by(**kwargs).one_or_none()

    @property
    def model_name(self):
        return self._model_name()

    @property
    def table_name(self):
        return self._table_name()

    @property
    def shortlink(self):
        pk_values = self.pk_values
        if not any(pk_values):
            return "new %s" % self.model_name
        else:
            pk_key = '-'.join(map(str, pk_values))
            return "%s #%s" % (self.model_name, pk_key)

    @property
    def header(self):
        return self.shortlink.replace('_', ' ').title()

    @property
    def show_url(self):
        return url_for(self.table_name + ".show_html", id=self.id)

    @property
    def show_link(self):
        return Markup('<a href="%s">%s</a>' % (self.show_url, self.shortlink))

    @property
    def index_url(self):
        return url_for(self.table_name + ".index_html")

    @property
    def create_url(self):
        return url_for(self.table_name + ".create_html")

    @property
    def update_url(self):
        return url_for(self.table_name + ".update_html", id=self.id)

    @property
    def edit_url(self):
        return url_for(self.table_name + ".edit_html", id=self.id)

    @property
    def delete_url(self):
        return url_for(self.table_name + ".delete_html", id=self.id)

    def column_dict(self):
        return {k: getattr(self, k) for k in self.__table__.c.keys() if hasattr(self, k)}

    def basic_json(self):
        return self._json(self.basic_attributes)

    def to_json(self):
        return self._json(self.json_attributes)

    def recreate_json(self):
        return self._json(self.recreate_attributes)

    def copy(self):
        """Return an uncommitted copy of the record."""
        return self.__class__(**self.column_dict())

    def compare(self, cmp):
        if self.__class__ != cmp.__class__:
            return False
        return all(getattr(self, col) == getattr(cmp, col) for col in self.all_columns)

    def attach(self, attr, record):
        setattr(self, attr, record)

    def update(self, data):
        for attr in self.basic_attributes:
            if attr in data:
                setattr(self, attr, data[attr])

    @property
    def pk_values(self):
        return tuple(getattr(self, key) for key in self.primary_keys)

    @classproperty(cached=False)
    def relations(cls):
        cls._populate_attributes()
        return getattr(cls, '__relations')

    @classmethod
    def fk_relations(cls):
        relations = []
        for key in cls.relations:
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
    def primary_key(cls):
        return cls.__table__.primary_key

    @classproperty(cached=True)
    def pk_cols(cls):
        return [c for c in cls.primary_key.columns]

    @classproperty(cached=True)
    def primary_keys(cls):
        return [t.name for t in cls.pk_cols]

    @classmethod
    def columns(cls):
        return [c for c in cls.__table__.columns]

    @classproperty(cached=True)
    def column_map(cls):
        return {c.name: c for c in cls.columns()}

    @classproperty(cached=True)
    def all_columns(cls):
        return [c.name for c in cls.columns()]

    @classproperty(cached=True)
    def base_columns(cls):
        return [k for k in cls.all_columns if len(cls.column_map[k].foreign_keys) == 0]

    @classproperty(cached=True)
    def fk_columns(cls):
        return [k for k in cls.all_columns if len(cls.column_map[k].foreign_keys) > 0]

    @classproperty(cached=True)
    def archive_columns(cls):
        return {k for k in cls.base_columns if k != 'id'}

    @classproperty(cached=False)
    def load_columns(cls):
        return cls.all_columns

    @classmethod
    def loads(cls, data, *args):
        return cls(**{k: json_deserialize(v) for (k, v) in data.items() if k in cls.load_columns})

    @classproperty(cached=True)
    def basic_attributes(cls):
        cls._populate_attributes()
        return getattr(cls, '__all_columns')

    @classproperty(cached=True)
    def relation_attributes(cls):
        return [relation.strip('_') for relation in cls.relations]

    @classproperty(cached=True)
    def searchable_attributes(cls):
        return cls.basic_attributes + cls.relation_attributes

    @classproperty(cached=False)
    def order_attributes(cls):
        return cls.basic_attributes

    @classproperty(cached=False)
    def json_attributes(cls):
        return cls.basic_attributes

    @classproperty(cached=False)
    def repr_attributes(cls):
        return cls.basic_attributes

    @classproperty(cached=True)
    def recreate_attributes(cls):
        return [attr for attr in cls.basic_attributes
                if attr not in cls.primary_keys
                and not isinstance(getattr(cls, attr).type, JSON)]

    @StaticProperty
    def rowid():
        return DB.column("rowid")

    # Private

    def __repr__(self):
        data = {}
        for attr in self.repr_attributes:
            data[attr] = getattr(self, attr)
            if isinstance(data[attr], bytes):
                data[attr] = f'blob({data[attr].hex()})'
        inner_string = ', '.join(f"{k}={repr(data[k])}" for k in self.repr_attributes)
        model_name = self.__class__.__name__
        return f"{model_name}({inner_string})"

    def _json(self, attributes):
        data = {}
        for attr in attributes:
            if isinstance(attr, tuple):
                key, attr = attr
            else:
                key = attr
            value = getattr(self, attr)
            if type(value) is datetime.datetime:
                data[key] = value if value is None else datetime.datetime.isoformat(value)
            elif type(value) is bytes:
                data[key] = value.hex()
            elif type(value) is _AssociationList:
                data[key] = list(value)
            elif type(value) is InstrumentedList:
                data[key] = [t.to_json() for t in value]
            elif hasattr(value, 'to_json'):
                data[key] = value.to_json()
            else:
                data[key] = value
        return data

    @classmethod
    def _populate_attributes(cls):
        if hasattr(cls, '__all_columns') and hasattr(cls, '__relations'):
            return
        class_attributes = set(dir(cls)).difference(dir(JsonModel))
        columns = cls.columns()
        basic_columns = []
        column_positions = {}
        relations = []
        for attr in class_attributes:
            if attr.startswith('_') and attr.endswith('_'):
                continue
            val = getattr(cls, attr)
            if not hasattr(val, 'property'):
                continue
            if isinstance(val.property, ColumnProperty):
                basic_columns.append(attr)
                column_positions[attr] = columns.index(val.property.columns[0])
            elif isinstance(val.property, RelationshipProperty):
                relations.append(attr)
        basic_columns.sort(key=lambda x: column_positions[x])
        setattr(cls, '__all_columns', basic_columns)
        setattr(cls, '__relations', relations)

    @classmethod
    def _model_name(cls):
        keyname = '__model_name_' + cls.__name__
        if not hasattr(cls, keyname):
            setattr(cls, keyname, re.sub(r'([a-z])([A-Z])', r'\1_\2', cls.__name__).lower())
        return getattr(cls, keyname)

    @classmethod
    def _table_name(cls):
        return cls.__table__.name

    _secondary_table = False
    _enum_model = False


# #### Private

def _sorted_dict(data):
    return dict(sorted(data.items(), key=lambda x: x[0]))
