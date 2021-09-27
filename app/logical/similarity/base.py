# APP\LOGICAL\SIMILARITY\BASE.PY

# ## PYTHON IMPORTS
from PIL import Image
import distance
import imagehash

# ## LOCAL IMPORTS
from ...models.similarity_data import SimilarityData, HASH_SIZE, TOTAL_BITS
from ..database.media_file_db import create_media_file_from_parameters, batch_delete_media_files, get_media_file_by_url
from ..utility import get_buffer_checksum
from ..file import create_directory, put_get_raw
from ..network import get_http_file


# ## FUNCTIONS

def hex_to_binary(inhex):
    return bin(int(inhex, 16))[2:].zfill(len(inhex * 4))


def get_image(file_path):
    image = Image.open(file_path)
    return image.convert("RGB")


def get_image_hash(image):
    return str(imagehash.whash(image, hash_size=HASH_SIZE))


def get_similarity_data_matches(image_hash, ratio, post_id=None):
    query = SimilarityData.query
    query = query.filter(
        SimilarityData.ratio_clause(ratio),
        SimilarityData.cross_similarity_clause2(image_hash)
    )
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
