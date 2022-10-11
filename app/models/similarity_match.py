# APP/MODELS/SIMILARITY_MATCH.PY

# ## LOCAL IMPORTS
from .. import DB
from .base import JsonModel


# ## CLASSES

class SimilarityPoolElement(JsonModel):
    # ## Declarations

    # #### Columns
    id = DB.Column(DB.Integer, primary_key=True)
    pool_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=False, index=True)
    sibling_id = DB.Column(DB.Integer, DB.ForeignKey('similarity_pool_element.id'), nullable=True)
    post_id = DB.Column(DB.Integer, DB.ForeignKey('post.id'), nullable=False)
    score = DB.Column(DB.Float, nullable=False)
    main = DB.Column(DB.Boolean, nullable=False)

    # #### Relationships
    # post <- Post (MtO)
    # sibling <- SimilarityPoolElement (OtO)


# ## INITIALIZATION

def initialize():
    from .post import Post
    SimilarityPoolElement.sibling = DB.relationship(SimilarityPoolElement, uselist=False, lazy=True,
                                                    remote_side=[SimilarityPoolElement.id])
    # Access the opposite side of the relationships to force the back references to be generated
    Post.image_hashes.property._configure_started
    Post.similarity_pool.property._configure_started
    SimilarityPoolElement.sibling.property._configure_started
    SimilarityPoolElement.set_relation_properties()
