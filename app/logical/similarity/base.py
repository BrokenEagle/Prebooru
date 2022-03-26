# APP/LOGICAL/SIMILARITY/BASE.PY

# ## PYTHON IMPORTS
from PIL import Image

# ## EXTERNAL IMPORTS
import distance
import imagehash

# ## LOCAL IMPORTS
from ...models.similarity_data import SimilarityData, HASH_SIZE, TOTAL_BITS


# ## FUNCTIONS

def hex_to_binary(inhex):
    return bin(int(inhex, 16))[2:].zfill(len(inhex * 4))


def get_image(file_path):
    image = Image.open(file_path)
    return image.convert("RGB")


def get_image_hash(image):
    return str(imagehash.whash(image, hash_size=HASH_SIZE))


def get_similarity_data_matches(image_hash, ratio, sim_clause=None, post_id=None):
    switcher = {
        'chunk': lambda image_hash: SimilarityData.chunk_similarity_clause(image_hash),
        'cross0': lambda image_hash: SimilarityData.cross_similarity_clause0(image_hash),
        'cross1': lambda image_hash: SimilarityData.cross_similarity_clause1(image_hash),
        'cross2': lambda image_hash: SimilarityData.cross_similarity_clause2(image_hash),
    }
    query = SimilarityData.query
    if isinstance(ratio, float):
        query = query.filter(SimilarityData.ratio_clause(ratio))
    if sim_clause != 'all':
        sim_clause = sim_clause if sim_clause in switcher else 'cross2'
        query = query.filter(switcher[sim_clause](image_hash))
    if post_id is not None:
        query = query.filter(SimilarityData.post_id != post_id)
    return query.all()


def filter_score_results(score_results):
    """Posts can have more than one image hash, so only return the one with the highest score"""
    seen = set()
    final_results = []
    score_results = sorted(score_results, key=lambda x: x['score'], reverse=True)
    for result in score_results:
        if result['post_id'] in seen:
            continue
        final_results.append(result)
        seen.add(result['post_id'])
    return final_results


def check_similarity_match_scores(similarity_results, image_hash, min_score):
    found_results = []
    image_binary_string = hex_to_binary(image_hash)
    for sresult in similarity_results:
        sresult_binary_string = hex_to_binary(sresult.image_hash)
        mismatching_bits = distance.hamming(image_binary_string, sresult_binary_string)
        miss_ratio = mismatching_bits / TOTAL_BITS
        score = round((1 - miss_ratio) * 100, 2)
        if score >= min_score:
            data = {
                'post_id': sresult.post_id,
                'score': score,
            }
            found_results.append(data)
    return sorted(found_results, key=lambda x: x['score'], reverse=True)
