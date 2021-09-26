# APP/SIMILARITY/SIMILARITY_POOL.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ##CLASSES

@dataclass
class SimilarityPoolElement(JsonModel):
    # ## Declarations

    # #### JSON format
    id: int
    pool_id: int
    post_id: int
    score: float

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    pool_id = DB.Column(DB.Integer, DB.ForeignKey('similarity_pool.id'), nullable=False)
    sibling_id = DB.Column(DB.Integer, DB.ForeignKey('similarity_pool_element.id'), nullable=True)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=False)
    score = DB.Column(DB.Float, nullable=False)

    # #### Relationships
    # pool <- SimilarityPool (MtO)
    # sibling <- SimilarityPoolElement (OtO)


# ## INITIALIZATION

def initialize():
    SimilarityPoolElement.sibling = DB.relationship(SimilarityPoolElement, uselist=False, lazy=True)
    SimilarityPoolElement.set_relation_properties()
