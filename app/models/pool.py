# APP/MODELS/POOL.PY

# ## PYTHON IMPORTS
from flask import Markup

# ## EXTERNAL IMPORTS
from sqlalchemy import func
from sqlalchemy.util import memoized_property
from sqlalchemy.ext.orderinglist import ordering_list

# ## PACKAGE IMPORTS
from config import DEFAULT_PAGINATE_LIMIT, MAXIMUM_PAGINATE_LIMIT

# ## LOCAL IMPORTS
from .pool_element import PoolElement
from .base import JsonModel, integer_column, text_column, boolean_column, timestamp_column, relationship, backref


# ## GLOBAL VARIABLES

SHOW_PAGINATE_LIMIT = min(100, MAXIMUM_PAGINATE_LIMIT)


# ## CLASSES

class Pool(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    name = text_column(nullable=False)
    element_count = integer_column(nullable=False)
    series = boolean_column(nullable=False)
    checked = timestamp_column(nullable=True)
    created = timestamp_column(nullable=False)
    updated = timestamp_column(nullable=False)

    # ## Relationships
    elements = relationship(PoolElement, order_by=PoolElement.position, uselist=True,
                            backref=backref('pool', uselist=False), cascade='all,delete',
                            collection_class=ordering_list('position'))

    # ## Instance properties

    @memoized_property
    def items(self):
        return [element.item for element in self.elements]

    @property
    def next_position(self):
        if self.element_count == 0:
            return 0
        return PoolElement.query.filter(PoolElement.pool_id == self.id)\
                                .with_entities(func.max(PoolElement.position)).scalar() + 1

    def element_paginate(self, pagenum=None, per_page=None, options=None):
        q = self._element_query
        if options is not None:
            q = q.options(options)
        q = q.order_by(PoolElement.position)
        per_page = min(per_page, SHOW_PAGINATE_LIMIT) if per_page is not None else DEFAULT_PAGINATE_LIMIT
        return q.count_paginate(per_page=per_page, page=pagenum)

    # ## Private

    @property
    def name_link(self):
        return Markup('<a href="%s">%s</a>' % (self.show_url, self.name))

    @property
    def _element_query(self):
        return PoolElement.query.filter_by(pool_id=self.id)

    def _get_element_count(self):
        return self._element_query.get_count()
