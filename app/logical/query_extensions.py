# APP/LOGICAL/QUERY_EXTENSIONS.PY

# ## PYTHON IMPORTS
from sqlalchemy import func
import sqlalchemy.orm

# ## PACKAGE IMPORTS
from config import DEFAULT_PAGINATE_LIMIT


# ## GLOBAL VARIABLES

INIT = False


# ## CLASSES

class CountPaginate():
    def __init__(self, query=None, page=1, per_page=DEFAULT_PAGINATE_LIMIT):
        self.query = query
        self.per_page = per_page
        self.page = max(page, 1)
        self.offset = (page - 1) * per_page
        self.items = self._GetItems()
        self.count = self._GetCount()
        self.pages = ((self.count - 1) // per_page) + 1

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
        return CountPaginate(query=self.query, page=self.page + 1, per_page=self.per_page) if self.has_next else None

    def prev(self):
        return CountPaginate(query=self.query, page=self.page - 1, per_page=self.per_page) if self.has_prev else None

    def _GetItems(self):
        return self.query.limit(self.per_page).offset(self.offset).all()

    def _GetCount(self):
        # Easy way to get an exact copy of a query
        self._count_query = self.query.filter()
        if len(self._count_query._where_criteria) == 0:
            model = self._count_query.column_descriptions[0]['entity']
            # Queries with no where criteria do not work correctly
            self._count_query = self._count_query.filter(model.id)
        # Using function count with scalar does not like loader options
        self._count_query._with_options = ()
        return self._count_query.get_count()


class LimitPaginate():
    """Pagination method for processing items which may be removed from the total as it gets processed."""
    def __init__(self, query=None, page=1, per_page=DEFAULT_PAGINATE_LIMIT, count=None, next_id=None, prev_id=None):
        self.query = query
        self.per_page = per_page
        self.page = page
        self.next_id = next_id
        self.prev_id = prev_id
        self.items = self._GetItems()
        self.current_count = self._GetCount()
        self.count = count or self.current_count
        self.pages = ((self.current_count - 1) // per_page) + 1
        self.first = ((page - 1) * per_page) + 1
        self.last = min(page * per_page, self.count)

    @property
    def has_next(self):
        return self.pages > 0 and len(self.items) > self.per_page

    @property
    def has_prev(self):
        return self.pages > 0 and len(self.items) > self.per_page

    @property
    def next_num(self):
        return self.page + 1

    @property
    def prev_num(self):
        return self.page - 1

    @property
    def next_sequential_id(self):
        return min([item.id for item in self.items]) if len(self.items) else None

    @property
    def prev_sequential_id(self):
        return max([item.id for item in self.items]) if len(self.items) else None

    def next(self):
        return LimitPaginate(query=self.query, page=self.next_num, per_page=self.per_page, count=self.count,
                             next_id=self.next_sequential_id) if self.has_next else None

    def prev(self):
        return LimitPaginate(query=self.query, page=self.prev_num, per_page=self.per_page, count=self.count,
                             prev_id=self.prev_sequential_id) if self.has_prev else None

    def _GetItems(self):
        model = _query_model(self.query)
        q = self.query
        if self.next_id:
            q = q.filter(model.id < self.next_id)
        elif self.prev_id:
            q = q.filter(model.id > self.prev_id)
        return q.limit(self.per_page).all()

    def _GetCount(self):
        return self.query.count()


# ## FUNCTIONS

# #### Initialization functions

def initialize():
    """This can only be set after the models have been initialized"""
    global INIT
    if not INIT:
        sqlalchemy.orm.Query._has_entity = _has_entity
        sqlalchemy.orm.Query.unique_join = unique_join
        sqlalchemy.orm.Query.get_count = get_count
        sqlalchemy.orm.Query.count_paginate = count_paginate
        sqlalchemy.orm.Query.limit_paginate = limit_paginate
        INIT = True


# #### Extension functions

def unique_join(self, model, *args, **kwargs):
    if not self._has_entity(model):
        self = self.join(model, *args, **kwargs)
    return self


def get_count(self):
    try:
        return self.with_entities(func.count()).scalar()
    except Exception:
        return self.count()


def count_paginate(self, page=1, per_page=DEFAULT_PAGINATE_LIMIT):
    return CountPaginate(query=self, page=page, per_page=per_page)


def limit_paginate(self, page=1, per_page=DEFAULT_PAGINATE_LIMIT):
    return LimitPaginate(query=self, page=page, per_page=per_page)


# #### Private functions

def _has_entity(self, model):
    current_joined_tables = [t[0] for t in self._legacy_setup_joins]
    return model.__table__ in current_joined_tables


def _query_model(query):
    return query.column_descriptions[0]['entity']
