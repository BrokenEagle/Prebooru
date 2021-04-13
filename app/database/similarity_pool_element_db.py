# APP/DATABASE/SIMILARITY_POOL_ELEMENT_DB.PY

# ## LOCAL IMPORTS
from .. import SESSION
from ..logical.utility import UniqueObjects
from ..similarity import SimilarityPoolElement


# ## FUNCTIONS

# #### Route DB functions

# ###### DELETE

def DeleteSimilarityPoolElement(similarity_pool_element):
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


def BatchDeleteSimilarityPoolElement(similarity_pool_elements):
    pool_element_ids = [element.id for element in similarity_pool_elements]
    pool_element_ids += [element.sibling_id for element in similarity_pool_elements if element.sibling_id is not None]
    similarity_pools = UniqueObjects(similarity_pool_elements + [element.sibling.pool for element in similarity_pool_elements if element.sibling_id is not None])  # This could maybe be done better
    SimilarityPoolElement.query.filter(SimilarityPoolElement.id.in_(pool_element_ids)).update({'sibling_id': None})
    SESSION.commit()
    SimilarityPoolElement.query.filter(SimilarityPoolElement.id.in_(pool_element_ids)).delete()
    SESSION.commit()
    for pool in similarity_pools:
        pool.element_count = pool._get_element_count()
    SESSION.commit()
