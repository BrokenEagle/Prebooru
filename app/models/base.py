# APP/BASE_MODEL.PY

# ## PYTHON IMPORTS
import datetime
from typing import List, _GenericAlias
from flask import url_for, Markup
from sqlalchemy.orm import RelationshipProperty, reconstructor
from sqlalchemy.util import memoized_property

# ## LOCAL IMPORTS
from .. import DB, SERVER_INFO
from ..config import HAS_EXTERNAL_IMAGE_SERVER, IMAGE_PORT


# ## FUNCTIONS

# #### Helper functions

def date_time_or_null(value):
    return value if value is None else datetime.datetime.isoformat(value)


def int_or_none(data):
    return data if data is None else int(data)


def str_or_none(data):
    return data if data is None else str(data)


def remove_keys(data, keylist):
    return {k: data[k] for k in data if k not in keylist}


# #### Network functions

def _external_server_url(urlpath):
    return 'http://' + SERVER_INFO.addr + ':' + str(IMAGE_PORT) + '/images/' + urlpath


def _internal_serval_url(urlpath):
    return url_for('images.send_file', path=urlpath)


image_server_url = _external_server_url if HAS_EXTERNAL_IMAGE_SERVER else _internal_serval_url


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


# ## CLASSES

class JsonModel(DB.Model):
    __abstract__ = True

    @classmethod
    def find(cls, id):
        return cls.query.filter_by(id=id).first()

    @property
    def model_name(self):
        return self.__table__.name

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
        return {k: getattr(self, k) for k in self.__table__.c.keys() if hasattr(self, k)}

    def to_json(self):
        fields = self.__dataclass_fields__
        data = {}
        for key in fields:
            value = getattr(self, key)
            type_func = fields[key].type
            if type_func is None:
                data[key] = None
            elif 'to_json' in dir(type_func):
                data[key] = value.to_json()
            elif type_func == List:
                data[key] = [t.to_json() for t in value]
            elif isinstance(type_func, _GenericAlias):
                subtype_func = type_func.__args__[0]
                data[key] = [(subtype_func(t.to_json()) if 'to_json' in dir(t) else subtype_func(t)) for t in value]
            else:
                data[key] = type_func(value)
        return data

    @classmethod
    def relations(cls):
        if not hasattr(cls, '_relation_keys'):
            primary_keys = [key for key in dir(cls) if not key.startswith('_')]
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
            setattr(cls, key + '_shortlink', property(lambda x: "%s #%d" % (table_name, getattr(x, relation_key)) if getattr(x, relation_key) is not None else "new %s" % table_name))
            setattr(cls, key + '_show_url', property(lambda x: url_for("%s.show_html" % table_name, id=getattr(x, relation_key)) if getattr(x, relation_key) is not None else None))
            setattr(cls, key + '_show_link', property(lambda x: Markup('<a href="%s">%s</a>' % (getattr(x, key + '_show_url'), getattr(x, key + '_shortlink'))) if getattr(x, relation_key) is not None else None))
