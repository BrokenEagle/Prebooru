# APP/MODELS/POOL_ELEMENT.PY

# ## PYTHON IMPORTS
import math

# ## EXTERNAL IMPORTS
from flask import url_for

# ## PACKAGE IMPORTS
from config import DEFAULT_PAGINATE_LIMIT
from utility.obj import classproperty, memoized_classproperty
from utility.data import swap_list_values

# ## LOCAL IMPORTS
from .. import DB
from .model_enums import PoolElementType
from .base import JsonModel, integer_column, enum_column, register_enum_column


# ## FUNCTIONS

def pool_element_create(item):
    if item.__table__.name == 'post':
        return PoolPost(item=item)
    if item.__table__.name == 'illust':
        return PoolIllust(item=item)
    if item.__table__.name == 'notation':
        return PoolNotation(item=item)
    raise Exception("Invalid pool type.")


def pool_element_delete(pool_id, item):
    table_name = item.__table__.name
    if table_name == 'post':
        element = PoolPost.query.filter_by(pool_id=pool_id, post_id=item.id).one_or_none()
    if table_name == 'illust':
        element = PoolIllust.query.filter_by(pool_id=pool_id, illust_id=item.id).one_or_none()
    if table_name == 'notation':
        element = PoolNotation.query.filter_by(pool_id=pool_id, notation_id=item.id).one_or_none()
    if element is None:
        raise Exception("%s #%d not found in pool #%d." % (table_name, item.id, pool_id))
    SESSION.delete(element)


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

    # ## Instance properties

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

    polymorphic_base = True

    # ## Private

    __mapper_args__ = {
        'polymorphic_identity': PoolElementType.pool_element.id,
        'polymorphic_on': type_id,
    }
    __table_args__ = (
        DB.CheckConstraint(
            "((post_id IS NULL) + (illust_id IS NULL) + (notation_id IS NULL)) = 2",
            name="null_check"),
    )


class PoolPost(PoolElement):
    # ## Columns
    illust_id = None
    notation_id = None

    # ## Relationships
    # (MtO) item [Post]

    # ## Class properties

    @classproperty
    def repr_attributes(cls):
        return ['id', 'pool_id', 'post_id', ('type', 'type_name')]

    polymorphic_base = False

    # #### Private

    __mapper_args__ = {
        'polymorphic_identity': PoolElementType.pool_post.id,
    }


class PoolIllust(PoolElement):
    # ## Columns
    post_id = None
    notation_id = None

    # ## Relationships
    # (MtO) item [Illust]

    # ## Class properties

    @classproperty
    def repr_attributes(cls):
        return ['id', 'pool_id', 'illust_id', ('type', 'type_name')]

    polymorphic_base = False

    # #### Private
    __mapper_args__ = {
        'polymorphic_identity': PoolElementType.pool_illust.id,
    }


class PoolNotation(PoolElement):
    # ## Columns
    post_id = None
    illust_id = None

    # ## Relationships
    # (MtO) item [Notation]

    # ## Class properties

    @classproperty
    def repr_attributes(cls):
        return ['id', 'pool_id', 'notation_id', ('type', 'type_name')]

    polymorphic_base = False

    # ## Private
    __mapper_args__ = {
        'polymorphic_identity': PoolElementType.pool_notation.id,
    }


# ## INITIALIZATION

def initialize():
    DB.Index(None, PoolElement.post_id, PoolElement.pool_id, unique=True,
             sqlite_where=PoolElement.post_id.is_not(None))
    DB.Index(None, PoolElement.illust_id, PoolElement.pool_id, unique=True,
             sqlite_where=PoolElement.illust_id.is_not(None))
    DB.Index(None, PoolElement.notation_id, PoolElement.pool_id, unique=True,
             sqlite_where=PoolElement.notation_id.is_not(None))
    PoolElement.polymorphic_columns = {
        'post_id': PoolPost,
        'illust_id': PoolIllust,
        'notation_id': PoolNotation,
    }
    PoolElement.polymorphic_relations = {
        'post': PoolPost,
        'illust': PoolIllust,
        'notation': PoolNotation,
    }
    register_enum_column(PoolElement, PoolElementType, 'type')
