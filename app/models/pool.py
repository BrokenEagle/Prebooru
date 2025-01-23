# APP/MODELS/POOL.PY

# ## PYTHON IMPORTS
from flask import Markup

# ## EXTERNAL IMPORTS
from sqlalchemy import func
from sqlalchemy.orm import lazyload, selectin_polymorphic
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from config import DEFAULT_PAGINATE_LIMIT, MAXIMUM_PAGINATE_LIMIT

# ## LOCAL IMPORTS
from .post import Post
from .illust import Illust
from .notation import Notation
from .pool_element import PoolElement, PoolPost, PoolIllust, PoolNotation, pool_element_create, pool_element_delete
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
    _elements = relationship(PoolElement, order_by=PoolElement.position, uselist=True,
                             backref=backref('pool', uselist=False), cascade='all,delete',
                             collection_class=ordering_list('position'))

    # ## Association proxies
    elements = association_proxy('_elements', 'item', creator=lambda item: pool_element_create(item))

    # ## Instance properties

    @property
    def next_position(self):
        if self.element_count == 0:
            return 0
        return PoolElement.query.filter(PoolElement.pool_id == self.id)\
                                .with_entities(func.max(PoolElement.position)).scalar() + 1

    def remove(self, item):
        pool_element_delete(self.id, item)

    def insert_before(self, insert_item, mark_item):
        pool_element = self._get_mark_element(mark_item)
        element_position = pool_element.position
        self.elements.insert(element_position, insert_item)

    def element_paginate(self, page=None, per_page=None, post_options=None, illust_options=None, notation_options=None):
        def _get_options(options):
            if options is None:
                return (lazyload('*'),)
            if type(options) is tuple:
                return options
            return (options,)
        q = self._element_query
        q = q.options(selectin_polymorphic(PoolElement, [PoolIllust, PoolPost, PoolNotation]))
        q = q.order_by(PoolElement.position)
        per_page = min(per_page, SHOW_PAGINATE_LIMIT) if per_page is not None else DEFAULT_PAGINATE_LIMIT
        page = q.count_paginate(per_page=per_page, page=page)
        post_ids = [element.post_id for element in page.items if element.type.name == 'pool_post']
        illust_ids = [element.illust_id for element in page.items if element.type.name == 'pool_illust']
        notation_ids = [element.notation_id for element in page.items if element.type.name == 'pool_notation']
        posts = Post.query.options(*_get_options(post_options)).filter(Post.id.in_(post_ids))\
                    .all() if len(post_ids) else []
        illusts = Illust.query.options(*_get_options(illust_options)).filter(Illust.id.in_(illust_ids))\
                        .all() if len(illust_ids) else []
        notations = Notation.query.options(*_get_options(notation_options)).filter(Notation.id.in_(notation_ids))\
                            .all() if len(notation_ids) else []
        page.elements = page.items
        page.items = []
        for i in range(0, len(page.elements)):
            page_element = page.elements[i]
            page_item = None
            if page_element.type.name == 'pool_post':
                page_item = next(filter(lambda x: x.id == page_element.post_id, posts), None)
            elif page_element.type.name == 'pool_illust':
                page_item = next(filter(lambda x: x.id == page_element.illust_id, illusts), None)
            elif page_element.type.name == 'pool_notation':
                page_item = next(filter(lambda x: x.id == page_element.notation_id, notations), None)
            if page_item is None:
                raise Exception("Missing pool element item: %s" % repr(page_element))
            page.items.append(page_item)
        return page

    # ## Private

    @property
    def name_link(self):
        return Markup('<a href="%s">%s</a>' % (self.show_url, self.name))

    @property
    def _element_query(self):
        return PoolElement.query.filter_by(pool_id=self.id)

    def _get_element_count(self):
        return self._element_query.get_count()

    def _get_mark_element(self, mark_item):
        pool_element = next(filter(lambda x: x.pool_id == self.id, mark_item._pools), None)
        if pool_element is None:
            raise Exception("Could not find mark item %s #%d in pool #%d")
        return pool_element
