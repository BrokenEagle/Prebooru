# APP/MODELS/SIMILARITY_POOL.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ## CLASSES

class SimilarityPoolElement(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    pool_id = DB.Column(DB.Integer, DB.ForeignKey('similarity_pool.id'), nullable=False)
    sibling_id = DB.Column(DB.Integer, DB.ForeignKey('similarity_pool_element.id'), nullable=True)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=False)
    score = DB.Column(DB.Float, nullable=False)

    # #### Relationships
    # pool <- SimilarityPool (MtO)
    # sibling <- SimilarityPoolElement (OtO)

    # ## Class properties

    basic_attributes = ['id', 'pool_id', 'sibling_id', 'post_id', 'score']
    json_attributes = basic_attributes


# ## INITIALIZATION

def initialize():
    SimilarityPoolElement.sibling = DB.relationship(SimilarityPoolElement, uselist=False, lazy=True)
    SimilarityPoolElement.set_relation_properties()
