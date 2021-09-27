# APP/LOGICAL/DATABASE/SIMILARITY_POOL_ELEMENT_DB.PY

# ## LOCAL IMPORTS
from ... import SESSION
from ..utility import unique_objects
from ...models import SimilarityPoolElement
from .base_db import update_column_attributes

# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['pool_id', 'post_id', 'score']

CREATE_ALLOWED_ATTRIBUTES = ['pool_id', 'post_id', 'score']


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


# ###### DELETE

def delete_similarity_pool_element(similarity_pool_element):
    sibling_pool_element = similarity_pool_element.sibling
    similarity_pool_element.sibling_id = None
    if sibling_pool_element is not None:
        sibling_pool_element.sibling_id = None
    SESSION.commit()
    main_pool = similarity_pool_element.pool
    SESSION.delete(similarity_pool_element)
    main_pool.element_count = main_pool._get_element_count()
    SESSION.commit()
    if sibling_pool_element is not None:
        sibling_pool = sibling_pool_element.pool
        SESSION.delete(sibling_pool_element)
        sibling_pool.element_count = sibling_pool._get_element_count()
        SESSION.commit()


def batch_delete_similarity_pool_element(similarity_pool_elements):
    if len(similarity_pool_elements) == 0:
        return
    # Get all of the affected pools to update their counts. This could maybe be done better
    sibling_pools = [element.sibling.pool for element in similarity_pool_elements if element.sibling_id is not None]
    similarity_pools = unique_objects([similarity_pool_elements[0].pool] + sibling_pools)
    pool_element_ids = [element.id for element in similarity_pool_elements]
    pool_element_ids += [element.sibling_id for element in similarity_pool_elements if element.sibling_id is not None]
    SimilarityPoolElement.query.filter(SimilarityPoolElement.id.in_(pool_element_ids)).update({'sibling_id': None})
    SESSION.commit()
    SimilarityPoolElement.query.filter(SimilarityPoolElement.id.in_(pool_element_ids)).delete()
    SESSION.commit()
    for pool in similarity_pools:
        pool.element_count = pool._get_element_count()
    SESSION.commit()
