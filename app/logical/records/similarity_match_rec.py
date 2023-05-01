# APP/LOGICAL/RECORDS/SIMILARITY_MATCH_REC.PY

# ## LOCAL IMPORTS
from ..database.post_db import update_post_from_parameters
from ..database.similarity_match_db import create_similarity_match_from_parameters,\
    update_similarity_match_from_parameters
from .image_hash_rec import get_image_hash_matches, check_image_match_scores, filter_score_results


# ## FUNCTIONS

def generate_similarity_matches(post, singular=False, printer=print):
    """"Singular indicates that only one post with no similarity matches is being processed."""
    _calculate_similarity_matches(post, singular, printer)
    update_post_from_parameters(post, {'simcheck': True}, commit=False)


# #### Private

def _calculate_similarity_matches(post, singular, printer):
    score_results = []
    for imghash in post.image_hashes:
        smatches = get_image_hash_matches(imghash.hash, imghash.ratio, sim_clause='cross2', post_id=imghash.post_id)
        score_results += check_image_match_scores(smatches, imghash.hash, 90.0)
    final_results = filter_score_results(score_results)
    printer("Similarity match results (post #%d): %d" % (post.id, len(final_results)))
    if len(final_results) == 0:
        return
    current_similarity_matches = post.similarity_matches if not singular else []
    for result in score_results:
        similarity_match = next((match for match in current_similarity_matches
                                 if match.forward_id == result['post_id']
                                 or match.reverse_id == result['post_id']), None)
        if similarity_match is None:
            similarity_match = create_similarity_match_from_parameters({'forward_id': post.id,
                                                                        'reverse_id': result['post_id'],
                                                                        'score': result['score']})
            current_similarity_matches.append(similarity_match)
        else:
            update_similarity_match_from_parameters(similarity_match, {'score': result['score']})
