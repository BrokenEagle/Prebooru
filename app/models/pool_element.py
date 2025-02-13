# APP/MODELS/POOL_ELEMENT.PY

# ## PYTHON IMPORTS
import math

# ## EXTERNAL IMPORTS
from flask import url_for
from sqlalchemy.util import memoized_property

# ## PACKAGE IMPORTS
from config import DEFAULT_PAGINATE_LIMIT
from utility.obj import classproperty, memoized_classproperty
from utility.data import swap_list_values

# ## LOCAL IMPORTS
from .. import DB
from .model_enums import PoolElementType
from .base import JsonModel, integer_column, enum_column, register_enum_column


# ## CLASSES

class PoolElement(JsonModel):
    # ## Columns
    id = integer_column(primary_key=True)
    pool_id = integer_column(foreign_key='pool.id', nullable=False, index=True)
    post_id = integer_column(foreign_key='post.id', nullable=True)
    illust_id = integer_column(foreign_key='illust.id', nullable=True)
    notation_id = integer_column(foreign_key='notation.id', nullable=True)
    position = integer_column(nullable=False)
    type_id = enum_column(foreign_key='pool_element_type.id', nullable=False)

    # ## Relationships
    # (MtO) pool [Pool]
    # (MtO) post [Post]
    # (MtO) illust [Illust]
    # (OtO) notation [Notation]

    # ## Instance properties

    @memoized_property
    def item(self):
        if self.type_name == 'pool_post':
            return self.post
        if self.type_name == 'pool_illust':
            return self.illust
        if self.type_name == 'pool_notation':
            return self.notation

    @property
    def position1(self):
        # Logic is position 0 based, but the display needs to be position 1 based
        return self.position + 1

    @property
    def page_url(self):
        page = math.ceil(self.position1 / DEFAULT_PAGINATE_LIMIT)
        return url_for('pool.show_html', id=self.pool_id, page=page)

    # ## Class properties

    @memoized_classproperty
    def repr_attributes(cls):
        mapping = {
            'type_id': ('type', 'type_name'),
        }
        return swap_list_values(super().repr_attributes, mapping)

    @classproperty
    def json_attributes(cls):
        return cls.repr_attributes

    __table_args__ = (
        DB.CheckConstraint(
            "((post_id IS NULL) + (illust_id IS NULL) + (notation_id IS NULL)) = 2",
            name="null_check"),
    )


# ## INITIALIZATION

def initialize():
    DB.Index(None, PoolElement.post_id, PoolElement.pool_id, unique=True,
             sqlite_where=PoolElement.post_id.is_not(None))
    DB.Index(None, PoolElement.illust_id, PoolElement.pool_id, unique=True,
             sqlite_where=PoolElement.illust_id.is_not(None))
    DB.Index(None, PoolElement.notation_id, PoolElement.pool_id, unique=True,
             sqlite_where=PoolElement.notation_id.is_not(None))
    register_enum_column(PoolElement, PoolElementType, 'type')
