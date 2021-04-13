# APP/SIMILARITY/SIMILARITY_POOL.PY

# ##PYTHON IMPORTS
from dataclasses import dataclass

# ##LOCAL IMPORTS
from .. import DB
from ..base_model import JsonModel


# ##CLASSES

@dataclass
class SimilarityPoolElement(JsonModel):
    # ## Declarations

    # #### SqlAlchemy
    __bind_key__ = 'similarity'

    # #### JSON format
    id: int
    pool_id: int
    post_id: int
    score: float

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    pool_id = DB.Column(DB.Integer, DB.ForeignKey('similarity_pool.id'), nullable=False)
    sibling_id = DB.Column(DB.Integer, DB.ForeignKey('similarity_pool_element.id'), nullable=True)
    post_id = DB.Column(DB.Integer, nullable=False)
    score = DB.Column(DB.Float, nullable=False)

    # #### Relationships
    # pool <- SimilarityPool (MtO)
    # sibling <- SimilarityPoolElement (OtO)


# INITIALIZATION

SimilarityPoolElement.sibling = DB.relationship(SimilarityPoolElement, uselist=False, lazy=True)
