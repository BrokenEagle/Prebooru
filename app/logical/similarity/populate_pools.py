# APP\LOGICAL\SIMILARITY\POOL.PY

# ## PYTHON IMPORTS
from sqlalchemy.orm import selectinload

# ## LOCAL IMPORTS
from ...similarity import SimilarityPool
from ...database.similarity_data_db import get_similarity_data_by_post_id
from ...database.similarity_pool_db import update_similarity_pool_element_count, get_or_create_similarity_pool,\
    get_similarity_pools_by_ids
from ...database.similarity_pool_element_db import create_similarity_pool_element_from_parameters,\
    update_similarity_pool_element_pairing
from .base import get_similarity_data_matches, check_similarity_match_scores, filter_score_results


# ## FUNCTIONS

def populate_similarity_pools(post, printer=print):
    simdata_items = get_similarity_data_by_post_id(post.id)
    score_results = []
    for simdata in simdata_items:
        smatches = get_similarity_data_matches(simdata.image_hash, simdata.ratio, simdata.post_id)
        score_results += check_similarity_match_scores(smatches, simdata.image_hash, 90.0)
    final_results = filter_score_results(score_results)
    main_pool = get_or_create_similarity_pool(post.id)
    printer("Similarity pool results (post #%d): %d" % (post.id, len(final_results)))
    if len(final_results) == 0:
        return
    sibling_post_ids = set(result['post_id'] for result in score_results)
    sibling_pools = [get_or_create_similarity_pool(post_id) for post_id in sibling_post_ids]                                # Creates similarity pools if they don't exist
    sibling_pools = get_similarity_pools_by_ids(sibling_post_ids, options=(selectinload(SimilarityPool.elements),))         # Load similarity pools with all elements loaded
    create_similarity_pairings(post.id, final_results, main_pool, sibling_pools)


def create_similarity_pairings(post_id, score_results, main_pool, sibling_pools):
    index_pool_by_post_id = {pool.post_id: pool for pool in sibling_pools}
    index_post_ids_by_post_id = {pool.post_id: [element.post_id for element in pool.elements] for pool in sibling_pools}
    main_post_ids = [element.post_id for element in main_pool.elements]
    for result in score_results:
        print("Creating sibling pairs (post #%d): %s" % (post_id, str(result)))
        if result['post_id'] in main_post_ids:
            spe1 = next(filter(lambda x: x.post_id == result['post_id'], main_pool.elements))
        else:
            spe1 = create_similarity_pool_element_from_parameters({'pool_id': main_pool.id, **result})
            update_similarity_pool_element_count(main_pool)
        sibling_pool = index_pool_by_post_id[result['post_id']]
        sibling_pool_post_ids = index_post_ids_by_post_id[result['post_id']] if result['post_id'] in index_post_ids_by_post_id else []
        if post_id in sibling_pool_post_ids:
            spe2 = next(filter(lambda x: x.post_id == post_id, sibling_pool.elements))
        else:
            spe2 = create_similarity_pool_element_from_parameters({'pool_id': sibling_pool.id, 'post_id': post_id, 'score': result['score']})
            update_similarity_pool_element_count(sibling_pool)
        print("Sibling pair: %d <-> %d" % (spe1.id, spe2.id))
        update_similarity_pool_element_pairing(spe1, spe2)
