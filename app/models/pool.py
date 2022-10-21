# APP/MODELS/POOL.PY

# ## PYTHON IMPORTS
from flask import Markup

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import lazyload, selectin_polymorphic
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.ext.associationproxy import association_proxy

# ## PACKAGE IMPORTS
from config import DEFAULT_PAGINATE_LIMIT, MAXIMUM_PAGINATE_LIMIT

# ## LOCAL IMPORTS
from .. import DB
from .post import Post
from .illust import Illust
from .notation import Notation
from .pool_element import PoolElement, PoolPost, PoolIllust, PoolNotation, pool_element_create, pool_element_delete
from .base import JsonModel, EpochTimestamp


# ## GLOBAL VARIABLES

SHOW_PAGINATE_LIMIT = min(100, MAXIMUM_PAGINATE_LIMIT)


# ## CLASSES

class Pool(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String(255), nullable=False)
    element_count = DB.Column(DB.Integer, nullable=False)
    series = DB.Column(DB.Boolean, nullable=False)
    created = DB.Column(EpochTimestamp(nullable=False), nullable=False)
    updated = DB.Column(EpochTimestamp(nullable=False), nullable=False)

    # #### Relationships
    _elements = DB.relationship(PoolElement, backref='pool', order_by=PoolElement.position, lazy=True,
                                collection_class=ordering_list('position'), cascade='all,delete')

    # #### Association proxies
    elements = association_proxy('_elements', 'item', creator=lambda item: pool_element_create(item))

    # ## Property methods

    # #### Private

    @property
    def name_link(self):
        return Markup('<a href="%s">%s</a>' % (self.show_url, self.name))

    @property
    def _element_query(self):
        return PoolElement.query.filter_by(pool_id=self.id)

    # ## Methods

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
        post_ids = [element.post_id for element in page.items if element.type == element.type_enum.pool_post]
        illust_ids = [element.illust_id for element in page.items if element.type == element.type_enum.pool_illust]
        notation_ids = [element.notation_id
                        for element in page.items
                        if element.type == element.type_enum.pool_notation]
        posts = Post.query.options(*_get_options(post_options)).filter(Post.id.in_(post_ids))\
                    .all() if len(post_ids) else []
        illusts = Illust.query.options(*_get_options(illust_options)).filter(Illust.id.in_(illust_ids))\
                        .all() if len(illust_ids) else []
        notations = Notation.query.options(*_get_options(notation_options)).filter(Notation.id.in_(notation_ids))\
                            .all() if len(notation_ids) else []
        for i in range(0, len(page.items)):
            page_item = page.items[i]
            if page_item.type == page_item.type_enum.pool_post:
                page.items[i] = next(filter(lambda x: x.id == page_item.post_id, posts), None)
            elif page_item.type == page_item.type_enum.pool_illust:
                page.items[i] = next(filter(lambda x: x.id == page_item.illust_id, illusts), None)
            elif page_item.type == page_item.type_enum.pool_notation:
                page.items[i] = next(filter(lambda x: x.id == page_item.notation_id, notations), None)
            if page.items[i] is None:
                raise Exception("Missing pool element item: %s" % repr(page_item))
        return page

    # #### Private

    def _get_element_count(self):
        return self._element_query.get_count()

    def _get_mark_element(self, mark_item):
        pool_element = next(filter(lambda x: x.pool_id == self.id, mark_item._pools), None)
        if pool_element is None:
            raise Exception("Could not find mark item %s #%d in pool #%d")
        return pool_element
