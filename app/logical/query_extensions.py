# APP/LOGICAL/QUERY_EXTENSIONS.PY

# ## PYTHON IMPORTS
import re
from types import SimpleNamespace
from functools import reduce

# ## EXTERNAL IMPORTS
from sqlalchemy import func
import sqlalchemy.orm
import flask_sqlalchemy

# ## PACKAGE IMPORTS
from config import DEFAULT_PAGINATE_LIMIT


# ## GLOBAL VARIABLES

INIT = False


# ## CLASSES

class CountPaginate():
    def __init__(self, query=None, page=1, per_page=DEFAULT_PAGINATE_LIMIT, distinct=False, count=True, expunge=False):
        self.query = query
        self.per_page = per_page
        self.distinct = distinct
        self.expunge = expunge
        self.page = max(page, 1)
        self.offset = (page - 1) * per_page
        if count:
            self.count = self._get_count() or 0
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
            return CountPaginate(query=self.query, page=self.page + 1, per_page=self.per_page, distinct=self.distinct,
                                 expunge=self.expunge)

    def prev(self):
        if self.has_prev:
            return CountPaginate(query=self.query, page=self.page - 1, per_page=self.per_page, distinct=self.distinct,
                                 expunge=self.expunge)

    def _get_items(self):
        if self.distinct:
            model = self.query.column_descriptions[0]['entity']
            q = self.query.group_by(*model.pk_cols)
        else:
            q = self.query
        q = q.limit(self.per_page).offset(self.offset)
        return q.allexp() if self.expunge else q.all()

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


class SequentialPaginate():
    def __init__(self, query=None, per_page=DEFAULT_PAGINATE_LIMIT, page=None, count=None, distinct=False,
                 min_id=None, max_id=None, expunge=False):
        self.query = query
        self.per_page = per_page
        self.distinct = distinct
        self.expunge = expunge
        self.current_count = self._get_count()
        self.count = count or self.current_count
        if self.current_count > 0:
            self.min_id = min_id or self._get_min_id()
            self.max_id = max_id or self._get_max_id()
            if page == 'oldest_first':
                self.direction = 'a'
                self.sequential_id = self.min_id - 1
            elif page == 'newest_first':
                self.direction = 'b'
                self.sequential_id = self.max_id + 1
            elif isinstance(page, str):
                match = re.match(r'^(a|b)(\d+)$', page)
                if match:
                    self.direction = match.group(1)
                    self.sequential_id = int(match.group(2))
                else:
                    raise Exception("Invalid sequential page number specified.")
            else:
                raise Exception("Invalid page specified.")
            self.items = self._get_items() if self.current_count > 0 else []
            self.page_min, self.page_max =\
                [self.items[0], self.items[-1]]\
                if self.direction == 'a' else\
                [self.items[-1], self.items[0]]
            if self.page_max.id == self.page_min.id:
                self.range = f'{self.page_min.shortlink}'
            elif self.direction == 'a':
                self.range = f'{self.page_min.shortlink} - {self.page_max.shortlink}'
            else:
                self.range = f'{self.page_max.shortlink} - {self.page_min.shortlink}'
        else:
            self.min_id = self.max_id = self.page_min = self.page_max = None
            self.items = []
            self.range = 'N/A'
            self.direction = None

    @property
    def above_pagenum(self):
        return f'a{self.page_max.id}' if self.current_count > 0 else None

    @property
    def below_pagenum(self):
        return f'b{self.page_min.id}' if self.current_count > 0 else None

    @property
    def has_next(self):
        if self.direction == 'a':
            return self.has_above
        if self.direction == 'b':
            return self.has_below
        return False

    @property
    def has_above(self):
        return self.max_id > self.page_max.id if self.current_count > 0 else False

    @property
    def has_below(self):
        return self.min_id < self.page_min.id if self.current_count > 0 else False

    def above(self):
        return SequentialPaginate(query=self.query, per_page=self.per_page, page=self.above_pagenum, count=self.count,
                                  min_id=self.min_id, max_id=self.max_id, distinct=self.distinct, expunge=self.expunge)

    def below(self):
        return SequentialPaginate(query=self.query, per_page=self.per_page, page=self.below_pagenum, count=self.count,
                                  min_id=self.min_id, max_id=self.max_id, distinct=self.distinct, expunge=self.expunge)

    @property
    def next(self):
        if self.direction == 'a':
            return self.above
        if self.direction == 'b':
            return self.below
        return None

    def _get_min_id(self):
        model = _query_model(self.query)
        return self.query.with_entities(model.id).order_by(model.id.asc()).limit(1).scalar()

    def _get_max_id(self):
        model = _query_model(self.query)
        return self.query.with_entities(model.id).order_by(model.id.desc()).limit(1).scalar()

    def _get_items(self):
        model = _query_model(self.query)
        if self.distinct:
            model = self.query.column_descriptions[0]['entity']
            q = self.query.group_by(*model.pk_cols)
        else:
            q = self.query
        if self.direction == 'a':
            q = q.filter(model.id > self.sequential_id).order_by(model.id.asc())
        else:
            q = q.filter(model.id < self.sequential_id).order_by(model.id.desc())
        q = q.limit(self.per_page)
        return q.allexp() if self.expunge else q.all()

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
        sqlalchemy.orm.Query.safe_filter = safe_filter
        sqlalchemy.orm.Query.get_count = get_count
        sqlalchemy.orm.Query.relation_count = relation_count
        sqlalchemy.orm.Query.distinct_count = distinct_count
        sqlalchemy.orm.Query.count_paginate = count_paginate
        sqlalchemy.orm.Query.sequential_paginate = sequential_paginate
        sqlalchemy.orm.Query.allexp = expunge_all
        sqlalchemy.orm.Query.all2 = secondary_all
        sqlalchemy.orm.Query.first2 = secondary_first
        sqlalchemy.orm.Query.one2 = secondary_one
        sqlalchemy.orm.Query.one_or_none2 = secondary_one_or_none
        flask_sqlalchemy.Pagination.first = paginate_first
        flask_sqlalchemy.Pagination.last = paginate_last
        INIT = True


# #### Extension functions

def safe_filter(self, *args):
    return self.filter(*(arg for arg in args if arg is not None))


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


def sequential_paginate(self, **kwargs):
    return SequentialPaginate(query=self, **kwargs)


def expunge_all(self):
    from .. import SESSION
    items = self.all()
    for item in items:
        SESSION.expunge(item)
    return items


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
