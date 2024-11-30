# APP/LOGICAL/QUERY_EXTENSIONS.PY

# ## PYTHON IMPORTS
from enum import Enum
from types import SimpleNamespace
from functools import reduce

# ## EXTERNAL IMPORTS
from sqlalchemy import func
from sqlalchemy.orm import RelationshipProperty
from sqlalchemy.orm.strategy_options import loader_option, _UnboundLoad
import sqlalchemy.orm
import flask_sqlalchemy

# ## PACKAGE IMPORTS
from config import DEFAULT_PAGINATE_LIMIT, USE_ENUMS


# ## GLOBAL VARIABLES

INIT = False


# ## CLASSES

class CountPaginate():
    def __init__(self, query=None, page=1, per_page=DEFAULT_PAGINATE_LIMIT, distinct=False, count=True):
        self.query = query
        self.per_page = per_page
        self.distinct = distinct
        self.page = max(page, 1)
        self.offset = (page - 1) * per_page
        if count:
            self.count = self._get_count()
            self.pages = ((self.count - 1) // per_page) + 1
            self.total = self.pages
            self.first = ((page - 1) * per_page) + 1
            self.last = min(page * per_page, self.count)
        self.items = self._get_items() if not count or self.count > 0 else []

    @property
    def has_next(self):
        return self.page < self.pages

    @property
    def has_prev(self):
        return self.page > 1

    @property
    def next_num(self):
        return self.page + 1 if self.has_next else None

    @property
    def prev_num(self):
        return self.page - 1 if self.has_prev else None

    def next(self):
        if self.has_next:
            return CountPaginate(query=self.query, page=self.page + 1, per_page=self.per_page, distinct=self.distinct)

    def prev(self):
        if self.has_prev:
            return CountPaginate(query=self.query, page=self.page - 1, per_page=self.per_page, distinct=self.distinct)

    def _get_items(self):
        if self.distinct:
            model = self.query.column_descriptions[0]['entity']
            q = self.query.group_by(*model.pk_cols)
        else:
            q = self.query
        return q.limit(self.per_page).offset(self.offset).all()

    def _get_count(self):
        # Easy way to get an exact copy of a query
        self._count_query = self.query.filter()
        if len(self._count_query._where_criteria) == 0:
            model = self._count_query.column_descriptions[0]['entity']
            # Queries with no where criteria do not work correctly
            self._count_query = self._count_query.filter(*model.pk_cols)
        # Using function count with scalar does not like loader options
        self._count_query._with_options = ()
        if self.distinct:
            # Keep it from rendering an unncessary DISTINCT outside of the count
            self._count_query._distinct_on = ()
            self._count_query._distinct = False
        return self._count_query.get_count() if not self.distinct else self._count_query.distinct_count()


class LimitPaginate():
    """Pagination method for processing items which may be removed from the total as it gets processed."""
    def __init__(self, query=None, page=1, per_page=DEFAULT_PAGINATE_LIMIT, count=None, distinct=False, next_id=None, prev_id=None):
        self.query = query
        self.per_page = per_page
        self.page = page
        self.next_id = next_id
        self.prev_id = prev_id
        self.distinct = distinct
        self.current_count = self._get_count()
        self.count = count or self.current_count
        self.items = self._get_items() if self.current_count > 0 else []
        self.pages = ((self.current_count - 1) // per_page) + 1
        self.total = ((self.count - 1) // per_page) + 1
        self.first = ((page - 1) * per_page) + 1
        self.last = min(page * per_page, self.count)
        self.next_sequential_id = min([item.id for item in self.items]) if len(self.items) else None
        self.prev_sequential_id = max([item.id for item in self.items]) if len(self.items) else None

    @property
    def has_next(self):
        return self.pages > 0 and len(self.items) >= self.per_page

    has_prev = has_next

    @property
    def next_num(self):
        return self.page + 1

    prev_num = next_num

    @property
    def prev_num(self):
        return self.page + 1

    def next(self):
        return LimitPaginate(query=self.query, page=self.next_num, per_page=self.per_page, count=self.count,
                             next_id=self.next_sequential_id, distinct=self.distinct) if self.has_next else None

    def prev(self):
        return LimitPaginate(query=self.query, page=self.prev_num, per_page=self.per_page, count=self.count,
                             prev_id=self.prev_sequential_id, distinct=self.distinct) if self.has_prev else None

    def _get_items(self):
        model = _query_model(self.query)
        if self.distinct:
            model = self.query.column_descriptions[0]['entity']
            q = self.query.group_by(*model.pk_cols)
        else:
            q = self.query
        if self.next_id:
            q = q.filter(model.id < self.next_id)
        elif self.prev_id:
            q = q.filter(model.id > self.prev_id)
        return q.order_by(model.id.desc()).limit(self.per_page).all()

    def _get_count(self):
        # Easy way to get an exact copy of a query
        self._count_query = self.query.filter()
        if len(self._count_query._where_criteria) == 0:
            model = self._count_query.column_descriptions[0]['entity']
            # Queries with no where criteria do not work correctly
            self._count_query = self._count_query.filter(*model.pk_cols)
        # Using function count with scalar does not like loader options
        self._count_query._with_options = ()
        if self.distinct:
            # Keep it from rendering an unncessary DISTINCT outside of the count
            self._count_query._distinct_on = ()
            self._count_query._distinct = False
        return self._count_query.get_count() if not self.distinct else self._count_query.distinct_count()


# ## FUNCTIONS

# #### Initialization functions

def initialize():
    """This can only be set after the models have been initialized"""
    global INIT
    if not INIT:
        sqlalchemy.orm.Query._has_entity = _has_entity
        sqlalchemy.orm.Query.unique_join = unique_join
        sqlalchemy.orm.Query.enum_join = enum_join
        sqlalchemy.orm.selectinload_enum = initialize_selectin_enum()._unbound_fn
        sqlalchemy.orm.Query.get_count = get_count
        sqlalchemy.orm.Query.relation_count = relation_count
        sqlalchemy.orm.Query.distinct_count = distinct_count
        sqlalchemy.orm.Query.count_paginate = count_paginate
        sqlalchemy.orm.Query.limit_paginate = limit_paginate
        sqlalchemy.orm.Query.all2 = secondary_all
        sqlalchemy.orm.Query.first2 = secondary_first
        sqlalchemy.orm.Query.one2 = secondary_one
        sqlalchemy.orm.Query.one_or_none2 = secondary_one_or_none
        flask_sqlalchemy.Pagination.first = paginate_first
        flask_sqlalchemy.Pagination.last = paginate_last
        INIT = True


def initialize_selectin_enum():
    @loader_option()
    def selectinload_enum(loadopt, attr):
        if not USE_ENUMS or not isinstance(attr.property, RelationshipProperty):
            loadopt.set_relationship_strategy(attr, {"lazy": "selectin"})
        return loadopt

    @selectinload_enum._add_unbound_fn
    def selectinload_enum(*keys):
        return _UnboundLoad._from_keys(_UnboundLoad.selectinload_enum, keys, False, {})

    return selectinload_enum


# #### Extension functions

def enum_join(self, model, *args, **kwargs):
    if not USE_ENUMS or not issubclass(model, Enum):
        self = self.unique_join(model, *args, **kwargs)
    return self


def unique_join(self, model, *args, **kwargs):
    if not self._has_entity(model):
        self = self.join(model, *args, **kwargs)
    return self


def get_count(self):
    try:
        return self.with_entities(func.count()).scalar()
    except Exception:
        return self.count()


def relation_count(self):
    entity = self.column_descriptions[0]['entity']
    try:
        return self.distinct().with_entities(entity.id).count()
    except Exception:
        return self.distinct().count()


def distinct_count(self):
    entity = self._raw_columns[0]
    concat_cols = _multiconcat(entity.primary_key.columns)
    return self.with_entities(func.count(concat_cols.distinct())).scalar()


def count_paginate(self, **kwargs):
    return CountPaginate(query=self, **kwargs)


def limit_paginate(self, page=1, per_page=DEFAULT_PAGINATE_LIMIT, distinct=False):
    return LimitPaginate(query=self, page=page, per_page=per_page, distinct=distinct)


def secondary_all(self):
    _secondary_check(self, 'all2')
    results = self.all()
    return [_result(item, _columns(self)) for item in results]


def secondary_first(self):
    _secondary_check(self, 'first2')
    item = self.first()
    return _result(item, _columns(self)) if item is not None else None


def secondary_one(self):
    _secondary_check(self, 'first2')
    item = self.one()
    return _result(item, _columns(self)) if item is not None else None


def secondary_one_or_none(self):
    _secondary_check(self, 'first2')
    item = self.one_or_none()
    return _result(item, _columns(self)) if item is not None else None


@property
def paginate_first(self):
    return ((self.page - 1) * self.per_page) + 1


@property
def paginate_last(self):
    return min((self.page * self.per_page), self.total)


# #### Private functions

def _has_entity(self, model):
    current_joined_tables = [t[0] for t in self._legacy_setup_joins]
    return model.__table__ in current_joined_tables


def _query_model(query):
    return query.column_descriptions[0]['entity']


def _secondary_check(query, name):
    if not query._raw_columns[0]._secondary_table:
        raise Exception(f"'{name}' only supported for secondary tables.")


def _result(item, columns):
    return SimpleNamespace(**{columns[0]: item[0], columns[1]: item[1]})


def _columns(query):
    return query._raw_columns[0].columns.keys()


def _multiconcat(columns):
    return reduce(lambda acc, x: getattr(acc, 'concat')(x), columns)
