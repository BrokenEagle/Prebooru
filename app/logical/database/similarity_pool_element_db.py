# APP/LOGICAL/DATABASE/SIMILARITY_POOL_ELEMENT_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import or_

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import SimilarityPoolElement
from .base_db import update_column_attributes

# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['pool_id', 'post_id', 'score', 'main']

CREATE_ALLOWED_ATTRIBUTES = ['pool_id', 'post_id', 'score', 'main']


# ## FUNCTIONS

# #### Route DB functions

# ###### CREATE

def create_similarity_pool_element_from_parameters(createparams):
    similarity_pool_element = SimilarityPoolElement()
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(similarity_pool_element, update_columns, createparams)
    print("[%s]: created" % similarity_pool_element.shortlink)
    return similarity_pool_element


# ###### UPDATE

def update_similarity_pool_element_pairing(similarity_pool_element_1, similarity_pool_element_2):
    similarity_pool_element_1.sibling_id = similarity_pool_element_2.id
    similarity_pool_element_2.sibling_id = similarity_pool_element_1.id
    SESSION.commit()


def set_similarity_element_main(element, val):
    element.main = val
    SESSION.commit()


# ###### DELETE

def delete_similarity_pool_element(similarity_pool_element):
    sibling_pool_element = similarity_pool_element.sibling
    similarity_pool_element.sibling_id = None
    if sibling_pool_element is not None:
        sibling_pool_element.sibling_id = None
    SESSION.commit()
    SESSION.delete(similarity_pool_element)
    if sibling_pool_element is not None:
        sibling_pool = sibling_pool_element.pool
        SESSION.delete(sibling_pool_element)


def delete_similarity_pool_elements_by_post_id(post_id):
    SimilarityPoolElement.query.filter(or_(SimilarityPoolElement.pool_id == post_id, SimilarityPoolElement.post_id == post_id)).update({'sibling_id': None})
    SESSION.commit()
    SimilarityPoolElement.query.filter(or_(SimilarityPoolElement.pool_id == post_id, SimilarityPoolElement.post_id == post_id)).delete()
    SESSION.commit()


def batch_delete_similarity_pool_element(similarity_pool_elements):
    element_ids = [element.id for element in similarity_pool_elements]
    SimilarityPoolElement.query.filter(SimilarityPoolElement.id.in_(element_ids)).update({'sibling_id': None})
    SESSION.commit()
    SimilarityPoolElement.query.filter(SimilarityPoolElement.id.in_(element_ids)).delete()
    SESSION.commit()


# ###### Query

def get_similarity_elements_by_post_id(post_id):
    return SimilarityPoolElement.query.filter_by(post_id=post_id).all()
