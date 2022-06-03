# APP/MODELS/SIMILARITY_POOL_ELEMENT.PY

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


# ## INITIALIZATION

def initialize():
    from .post import Post
    from .similarity_pool import SimilarityPool
    SimilarityPoolElement.sibling = DB.relationship(SimilarityPoolElement, uselist=False, lazy=True, remote_side=[SimilarityPoolElement.id])
    # Access the opposite side of the relationships to force the back references to be generated
    Post.similarity_data.property._configure_started
    SimilarityPool.elements.property._configure_started
    SimilarityPoolElement.sibling.property._configure_started
    SimilarityPoolElement.set_relation_properties()
