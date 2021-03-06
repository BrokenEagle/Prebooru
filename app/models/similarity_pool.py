# APP/MODELS/SIMILARITY_POOL.PY

# ## EXTERNAL IMPORTS
from sqlalchemy.orm import selectinload, lazyload

# ## PACKAGE IMPORTS
from config import DEFAULT_PAGINATE_LIMIT, MAXIMUM_PAGINATE_LIMIT

# ## LOCAL IMPORTS
from .. import DB
from .similarity_pool_element import SimilarityPoolElement
from .base import JsonModel


# ## GLOBAL VARIABLES

SHOW_PAGINATE_LIMIT = min(100, MAXIMUM_PAGINATE_LIMIT)


# ## CLASSES

class SimilarityPool(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=False)
    element_count = DB.Column(DB.Integer, nullable=False)
    created = DB.Column(DB.DateTime(timezone=False), nullable=False)
    updated = DB.Column(DB.DateTime(timezone=False), nullable=False)

    # #### Relationships
    elements = DB.relationship(SimilarityPoolElement, lazy=True, cascade="all, delete",
                               backref=DB.backref('pool', lazy=True, uselist=False))

    # ## Property methods

    # #### Private

    @property
    def _element_query(self):
        return SimilarityPoolElement.query.filter_by(pool_id=self.id)

    # ## Methods

    def element_paginate(self, page=None, per_page=None, post_options=lazyload('*')):
        q = self._element_query
        q = q.options(selectinload(SimilarityPoolElement.post),
                      selectinload(SimilarityPoolElement.sibling).selectinload(SimilarityPoolElement.pool))
        q = q.order_by(SimilarityPoolElement.score.desc())
        per_page = min(per_page, SHOW_PAGINATE_LIMIT) if per_page is not None else DEFAULT_PAGINATE_LIMIT
        page = q.count_paginate(per_page=per_page, page=page)
        return page

    def append(self, post_id, score):
        self._create_or_update_element(post_id, score)
        DB.session.commit()

    def update(self, results):
        for result in results:
            self._create_or_update_element(**result)
        DB.session.commit()

    # #### Private

    def _get_element_count(self):
        return self._element_query.get_count()

    def _create_or_update_element(self, post_id, score):
        element = next(filter(lambda x: x.post_id == post_id, self.elements), None)
        if element is None:
            element = SimilarityPoolElement(pool_id=self.id, post_id=post_id, score=score)
            DB.session.add(element)
        else:
            element.score = score
        return element
