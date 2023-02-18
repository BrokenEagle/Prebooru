# APP/MODELS/BASE.PY

# ## PYTHON IMPORTS
import re
import enum
import json
import zlib
import datetime

# ## EXTERNAL IMPORTS
from flask import url_for, Markup
from sqlalchemy.dialects.sqlite import DATETIME
from sqlalchemy.orm import RelationshipProperty, ColumnProperty
from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.ext.associationproxy import _AssociationList

# ## PACKAGE IMPORTS
from config import HAS_EXTERNAL_IMAGE_SERVER, IMAGE_PORT, USE_ENUMS
from utility.time import process_utc_timestring, datetime_from_epoch, datetime_to_epoch
from utility.obj import classproperty, StaticProperty

# ## LOCAL IMPORTS
from .. import DB, SESSION, SERVER_INFO


# ## GLOBAL VARIABLES

ISODATETIME_RG = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')


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


def get_relation_definitions(*args, **kwargs):
    if USE_ENUMS:
        return _get_relation_definitions_use_enums(*args, **kwargs)
    else:
        return _get_relation_definitions_use_models(*args, **kwargs)


def secondarytable(*args):
    @property
    def _query(self):
        return SESSION.query(self)

    table = DB.Table(*args, sqlite_with_rowid=False)
    table.__class__.query = _query
    table._model_name = lambda: args[0]
    table._secondary_table = True
    for col in table.columns.keys():
        setattr(table, col, getattr(table.c, col))
    return table


# ## CLASSES

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
    """
    Enables passing in a Python enum and storing the enum's *value* in the database.
    The default would have stored the enum's *name* (ie the string).
    """
    impl = DB.Integer
    cache_ok = True

    def __init__(self, enumtype, colname=None, tblname=None, nullable=False):
        super(IntEnum, self).__init__()
        self._enumtype = enumtype
        self._enumname = enumtype.__name__
        self._names = [e.name for e in self._enumtype]
        self._values = [e.id for e in self._enumtype]
        self._nullable = nullable
        self._colname = colname
        self._tblname = tblname

    def process_bind_param(self, value, dialect):
        if value in self._values:
            return value
        if value in self._names:
            return self._enumtype[value].value
        if isinstance(value, self._enumtype):
            return value.id
        if value is None and self._nullable:
            return None
        msg = f"Illegal value {repr(value)} to bind for enum {self._enumname} to [{self._tblname}:{self._colname}]."
        raise ValueError(msg)

    def process_result_value(self, value, dialect):
        if value in self._values:
            return self._enumtype(value)
        if value is None and self._nullable:
            return None
        msg = f"Illegal value {repr(value)} found in DB for enum {self._enumname} on [{self._tblname}:{self._colname}]."
        raise ValueError(msg)


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

    @classmethod
    def find_by_key(cls, key):
        return None

    @classmethod
    def find_rel_by_key(cls, rel, key, value):
        return None

    @property
    def key(self):
        return None

    @property
    def model_name(self):
        return self._model_name()

    @property
    def table_name(self):
        return self._table_name()

    @property
    def shortlink(self):
        return "%s #%d" % (self.model_name, self.id) if self.id is not None else "new %s" % self.model_name

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

    def archive_dict(self):
        return {k: json_serialize(self, k) for k in self.archive_columns if hasattr(self, k)}

    def basic_json(self, id_enum=False):
        return self._json(self.basic_attributes, id_enum)

    def to_json(self, id_enum=False):
        return self._json(self.json_attributes, id_enum)

    def copy(self):
        """Return an uncommitted copy of the record."""
        return self.__class__(**self.column_dict())

    def attach(self, attr, record):
        setattr(self, attr, record)

    @classproperty(cached=False)
    def relations(cls):
        cls._populate_attributes()
        return getattr(cls, '__relations')

    @classproperty(cached=True)
    def mandatory_fk_relations(cls):
        mandatory = []
        for rel in cls.fk_relations():
            relcol = next(iter(getattr(cls, rel).property.local_columns))
            if not relcol.nullable:
                mandatory.append(rel)
        return mandatory

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
        return [k for k in cls.base_columns if k != 'id']

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

    def _json(self, attributes, id_enum):
        data = {}
        for attr in attributes:
            value = getattr(self, attr)
            if type(value) is datetime.datetime:
                data[attr] = value if value is None else datetime.datetime.isoformat(value)
            elif type(value) is bytes:
                data[attr] = value.hex()
            elif isinstance(value, enum.Enum):
                if id_enum:
                    key = attr if attr.endswith('_id') else attr + '_id'
                    data[key] = value.id
                else:
                    key = attr.strip('_id')
                    data[key] = value.name
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

def _get_relation_definitions_use_enums(enm, relname=None, colname=None, tblname=None, nullable=None, **kwargs):
    if relname is None:
        raise Exception(f"Relation name is not defined for relation definition on {enm}.")
    baseval = DB.Column(colname,
                        IntEnum(enm, nullable=nullable, colname=colname, tblname=tblname),
                        nullable=nullable)

    @property
    def idval(self):
        attr = getattr(self, relname)
        return attr.value if attr is not None else None

    @idval.setter
    def idval(self, value):
        setattr(self, relname, enm(value) if value is not None else None)

    @property
    def nameval(self):
        attr = getattr(self, relname)
        return attr.name if attr is not None else None

    @nameval.setter
    def nameval(self, value):
        setattr(self, relname, enm[value] if value is not None else None)

    @classmethod
    def filter(cls, relattr, op, *args):
        if relattr is None:
            return getattr(baseval, op)(*args)
        else:
            rel = getattr(cls, relname)
            return _enum_filter(enm, rel, relattr, op, *args)

    @classmethod
    def colval(cls):
        return getattr(cls, relname)

    return baseval, idval, nameval, enm, filter, colval


def _get_relation_definitions_use_models(rel, colname=None, relcol=None, backname=None, nullable=None, **kwargs):
    if relcol is None:
        raise Exception(f"Relation column is not defined for relation definition on {rel}.")
    idval = DB.Column(DB.INTEGER, DB.ForeignKey(getattr(rel, relcol)), nullable=nullable)
    relation_kw = {
        'lazy': True,
        'foreign_keys': [idval],
    }
    if backname is not None:
        relation_kw['backref'] = DB.backref(backname, lazy=True)
    baseval = DB.relation(rel, **relation_kw)

    @property
    def nameval(self):
        id = getattr(self, colname)
        return rel.by_id(id).name if id is not None else None

    @nameval.setter
    def nameval(self, value):
        setattr(self, colname, rel.by_name(value).id if value is not None else None)

    @classmethod
    def filter(cls, relattr, op, *args):
        if relattr is None:
            enum_op = getattr(idval, op)
        else:
            enum_op = getattr(getattr(rel, relattr), op)
        return enum_op(*args)

    @classmethod
    def colval(cls):
        return getattr(cls, colname)

    return baseval, idval, nameval, rel, filter, colval


def _enum_filter(enm, rel, relattr, op, *args):
    enum_op = getattr(rel, op)
    if type(args[0]) in (set, list, tuple):
        if relattr == 'id':
            arg = [enm(a) for a in args[0]]
        elif relattr == 'name':
            arg = [enm[a] for a in args[0]]
    elif args[0] is not None:
        if relattr == 'id':
            arg = enm(args[0])
        elif relattr == 'name':
            arg = enm[args[0]]
    else:
        arg = args[0]
    return enum_op(arg, *args[1:])
