# APP/LOGICAL/SIMILARITY/POPULATE_POOLS.PY

# ## PYTHON IMPORTS
from sqlalchemy.orm import selectinload

# ## LOCAL IMPORTS
from ...models import Post
from ..database.image_hash_db import get_image_hash_by_post_id
from ..database.similarity_pool_element_db import create_similarity_pool_element_from_parameters,\
    update_similarity_pool_element_pairing, set_similarity_element_main, delete_similarity_pool_element
from .base import get_image_hash_matches, check_image_match_scores, filter_score_results


# ## FUNCTIONS

def populate_similarity_pools(main_post, printer=print):
    imghash_items = get_image_hash_by_post_id(main_post.id)
    score_results = []
    for imghash in imghash_items:
        smatches = get_image_hash_matches(imghash.hash, imghash.ratio, sim_clause='cross2', post_id=imghash.post_id)
        score_results += check_image_match_scores(smatches, imghash.hash, 90.0)
    final_results = filter_score_results(score_results)
    printer("Similarity pool results (post #%d): %d" % (main_post.id, len(final_results)))
    if len(final_results) == 0:
        return
    sibling_post_ids = set(result['post_id'] for result in score_results)
    sibling_posts = Post.query.options(selectinload(Post.similarity_pool)).filter(Post.id.in_(sibling_post_ids)).all()
    for result in score_results:
        spe1 = next((element for element in main_post.similarity_pool if element.post_id == result['post_id']), None)
        if spe1 is None:
            spe1 = create_similarity_pool_element_from_parameters({'pool_id': main_post.id, 'main': True, **result})
        sibling_post = next(post for post in sibling_posts if post.id == result['post_id'])
        spe2 = next((element for element in sibling_post.similarity_pool if element.post_id == main_post.id), None)
        if spe2 is None:
            params = {'pool_id': sibling_post.id, 'post_id': main_post.id, 'score': result['score'], 'main': False}
            spe2 = create_similarity_pool_element_from_parameters(params)
        print("Sibling pair: %d <-> %d" % (spe1.id, spe2.id))
        update_similarity_pool_element_pairing(spe1, spe2)
