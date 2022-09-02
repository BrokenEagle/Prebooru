# APP/LOGICAL/DATABASE/SIMILARITY_POOL_DB.PY

import threading

# ## PACKAGE IMPORTS
from utility.time import get_current_time
from utility.print import print_error

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import SimilarityPool
from .similarity_pool_element_db import get_similarity_elements_by_post_id, batch_delete_similarity_pool_element
from .base_db import update_column_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['post_id', 'element_count']

CREATE_ALLOWED_ATTRIBUTES = ['post_id']
UPDATE_ALLOWED_ATTRIBUTES = ['element_count']

COUNT_SEMAPHORE = threading.Semaphore(5)
COUNT_POOL_IDS = set()


# ## FUNCTIONS

# #### DB functions

# ###### CREATE

def create_similarity_pool_from_parameters(createparams):
    current_time = get_current_time()
    similarity_pool = SimilarityPool(element_count=0, created=current_time, updated=current_time)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(similarity_pool, update_columns, createparams)
    print("[%s]: created" % similarity_pool.shortlink)
    return similarity_pool


# ###### UPDATE

def update_similarity_pool_from_parameters(similarity_pool, updateparams):
    update_results = []
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(update_column_attributes(similarity_pool, update_columns, updateparams))
    if any(update_results):
        print("[%s]: updated" % similarity_pool.shortlink)
        similarity_pool.updated = get_current_time()
        SESSION.commit()


def update_similarity_element_count(similarity_pool):
    # Executed in a separate thread to keep from delaying the main thread
    def _update(pool_id):
        COUNT_SEMAPHORE.acquire()
        try:
            similarity_pool = SimilarityPool.find(pool_id)
            if similarity_pool is None:
                return
            similarity_pool.element_count = similarity_pool._get_element_count()
            SESSION.commit()
        except Exception as e:
            print_error("Error updating similarity element count:", repr(e))
        finally:
            COUNT_POOL_IDS.discard(pool_id)
            COUNT_SEMAPHORE.release()

    if similarity_pool.id in COUNT_POOL_IDS:
        return
    COUNT_POOL_IDS.add(similarity_pool.id)
    threading.Thread(target=_update, args=(similarity_pool.id,)).start()


# ###### DELETE

def delete_similarity_pool_by_post_id(post_id):
    similarity_pool = SimilarityPool.query.filter(SimilarityPool.post_id == post_id).first()
    if similarity_pool is None:
        return
    sibling_elements = get_similarity_elements_by_post_id(post_id)
    total_elements = similarity_pool.elements + sibling_elements
    if len(total_elements) > 0:
        sibling_pool_ids = [element.pool_id for element in sibling_elements]
        batch_delete_similarity_pool_element(similarity_pool.elements + sibling_elements)
        sibling_pools = SimilarityPool.query.filter(SimilarityPool.id.in_(sibling_pool_ids)).all()
        for pool in sibling_pools:
            update_similarity_element_count(pool)
    SESSION.delete(similarity_pool)
    SESSION.commit()


# #### Misc functions

def get_similarity_pools_by_ids(sibling_post_ids, options=None):
    query = SimilarityPool.query
    if options is not None:
        query = query.options(*options)
    query = query.filter(SimilarityPool.post_id.in_(sibling_post_ids))
    return query.all()


def get_or_create_similarity_pool(post_id):
    similarity_pool = SimilarityPool.query.filter(SimilarityPool.post_id == post_id).first()
    if similarity_pool is None:
        similarity_pool = create_similarity_pool_from_parameters({'post_id': post_id})
    return similarity_pool
