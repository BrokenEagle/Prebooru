# APP/LOGICAL/DATABASE/SIMILARITY_POOL_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import SimilarityPool
from .similarity_pool_element_db import batch_delete_similarity_pool_element
from .base_db import update_column_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['post_id', 'element_count']

CREATE_ALLOWED_ATTRIBUTES = ['post_id']
UPDATE_ALLOWED_ATTRIBUTES = ['element_count']


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


def update_similarity_pool_element_count(similarity_pool):
    update_similarity_pool_from_parameters(similarity_pool, {'element_count': similarity_pool._get_element_count()})


# ###### DELETE

def delete_similarity_pool_by_post_id(post_id):
    similarity_pool = SimilarityPool.query.filter(SimilarityPool.post_id == post_id).first()
    if similarity_pool is None:
        return
    batch_delete_similarity_pool_element(similarity_pool.elements)
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
