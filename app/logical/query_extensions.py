# APP/LOGICAL/UNSHORTENLINK.PY

# ##PYTHON IMPORTS
import sqlalchemy.orm
from sqlalchemy import func


# ##GLOBAL VARIABLES

INIT = False


class CountPaginate():
    def __init__(self, query=None, page=1, per_page=20):
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
        self._count_query = self.query.filter()  # Easy way to get an exact copy of a query
        if len(self._count_query._where_criteria) == 0:
            model = self._count_query.column_descriptions[0]['entity']
            self._count_query = self._count_query.filter(model.id)  # Queries with no where criteria do not work correctly
        self._count_query._with_options = ()  # Using function count with scalar does not like loader options
        return self._count_query.get_count()


# ##FUNCTIONS

# #### Initialization functions

def Initialize():
    """This can only be set after the models have been initialized"""
    global INIT
    if not INIT:
        sqlalchemy.orm.Query._has_entity = _has_entity
        sqlalchemy.orm.Query.unique_join = unique_join
        sqlalchemy.orm.Query.get_count = get_count
        sqlalchemy.orm.Query.count_paginate = count_paginate
        INIT = True


# #### Extension functions

def unique_join(self, model, *args, **kwargs):
    if not self._has_entity(model):
        self = self.join(model, *args, **kwargs)
    return self


def get_count(self):
    return self.with_entities(func.count()).scalar()


def count_paginate(self, page=1, per_page=20):
    return CountPaginate(query=self, page=page, per_page=per_page)


# #### Private functions

def _has_entity(self, model):
    current_joined_tables = [t[0] for t in self._legacy_setup_joins]
    return model.__table__ in current_joined_tables
