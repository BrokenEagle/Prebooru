# APP/MODELS/POOL_ELEMENT.PY

# ## PYTHON IMPORTS
import math

# ## EXTERNAL IMPORTS
from flask import url_for

# ## LOCAL IMPORTS
from .. import DB, SESSION
from .base import JsonModel


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
        element = PoolPost.query.filter_by(pool_id=pool_id, post_id=item.id).first()
    if table_name == 'illust':
        element = PoolIllust.query.filter_by(pool_id=pool_id, illust_id=item.id).first()
    if table_name == 'notation':
        element = PoolNotation.query.filter_by(pool_id=pool_id, notation_id=item.id).first()
    if element is None:
        raise Exception("%s #%d not found in pool #%d." % (table_name, item.id, pool_id))
    SESSION.delete(element)


# ## CLASSES

class PoolElement(JsonModel):
    # ## Declarations

    # #### JSON format
    id: int
    pool_id: int
    position: int
    type: str

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    pool_id = DB.Column(DB.Integer, DB.ForeignKey('pool.id'), nullable=False)
    position = DB.Column(DB.Integer, nullable=False)
    type = DB.Column(DB.String(50))

    # ## Relationships
    # pool <- Pool (MtO)

    # ## Property methods

    @property
    def position1(self):
        # Logic is position 0 based, but the display needs to be position 1 based
        return self.position + 1

    @property
    def page_url(self):
        page = math.ceil(self.position1 / 20)
        return url_for('pool.show_html', id=self.pool_id, page=page)

    # ## Class properties

    searchable_attributes = ['id', 'pool_id', 'position', 'type', 'post_id', 'illust_id', 'notation_id']
    basic_attributes = ['id', 'pool_id', 'position', 'type']
    json_attributes = basic_attributes

    # #### Private
    __tablename__ = 'pool_element'
    __mapper_args__ = {
        'polymorphic_identity': 'pool_element',
        "polymorphic_on": type
    }


class PoolPost(PoolElement):
    # ## Declarations

    # #### Columns
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=True)

    # ## Relationships
    # item <- Post (MtO)

    # ## Class properties

    basic_attributes = PoolElement.basic_attributes + ['post_id']
    json_attributes = basic_attributes

    # #### Private
    __tablename__ = 'pool_post'
    __mapper_args__ = {
        'polymorphic_identity': 'pool_post',
    }


class PoolIllust(PoolElement):
    # ## Declarations

    # #### Columns
    illust_id = DB.Column(DB.Integer, DB.ForeignKey('illust.id'), nullable=True)

    # ## Relationships
    # item <- Illust (MtO)

    # ## Class properties

    basic_attributes = PoolElement.basic_attributes + ['illust_id']
    json_attributes = basic_attributes

    # #### Private
    __tablename__ = 'pool_illust'
    __mapper_args__ = {
        'polymorphic_identity': 'pool_illust',
    }


class PoolNotation(PoolElement):
    # ## Declarations

    # #### Columns
    notation_id = DB.Column(DB.Integer, DB.ForeignKey('notation.id'), nullable=True)

    # ## Relationships
    # item <- Notation (OtO)

    # ## Class properties

    basic_attributes = PoolElement.basic_attributes + ['notation_id']
    json_attributes = basic_attributes

    # #### Private
    __tablename__ = 'pool_notation'
    __mapper_args__ = {
        'polymorphic_identity': 'pool_notation',
    }


# ## INITIALIZATION

def initialize():
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
