# APP/LOGICAL/SIMILARITY/BASE.PY

# ## PYTHON IMPORTS
from PIL import Image

# ## EXTERNAL IMPORTS
import distance
import imagehash

# ## LOCAL IMPORTS
from ...models.image_hash import ImageHash, HASH_SIZE, TOTAL_BITS


# ## FUNCTIONS

def hex_to_binary(inhex):
    return bin(int(inhex, 16))[2:].zfill(len(inhex * 4))


def img_hash_to_bytes(img_hash):
    bin_str = ''.join('1' if i else '0' for i in img_hash.hash.flatten())
    return bytes(int(bin_str[i: i + 8], 2) for i in range(0, len(bin_str), 8))


def bytes_to_binary(byte_obj):
    return bin(int(byte_obj.hex(), 16))[2:].zfill(len(byte_obj * 8))


def get_image(file_path):
    image = Image.open(file_path)
    return image.convert("RGB")


def get_image_hash(image):
    return img_hash_to_bytes(imagehash.whash(image, hash_size=HASH_SIZE))


def get_image_hash_matches(image_hash, ratio, sim_clause=None, post_id=None):
    switcher = {
        'chunk': lambda image_hash: ImageHash.chunk_similarity_clause(image_hash),
        'cross0': lambda image_hash: ImageHash.cross_similarity_clause0(image_hash),
        'cross1': lambda image_hash: ImageHash.cross_similarity_clause1(image_hash),
        'cross2': lambda image_hash: ImageHash.cross_similarity_clause2(image_hash),
    }
    query = ImageHash.query
    if isinstance(ratio, float):
        query = query.filter(ImageHash.ratio_clause(ratio))
    if sim_clause != 'all':
        query = query.filter(switcher[sim_clause](image_hash))
    if post_id is not None:
        query = query.filter(ImageHash.post_id != post_id)
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


def check_image_match_scores(image_match_results, image_hash, min_score):
    found_results = []
    image_binary_string = bytes_to_binary(image_hash)
    for image_match in image_match_results:
        image_match_binary_string = bytes_to_binary(image_match.hash)
        mismatching_bits = distance.hamming(image_binary_string, image_match_binary_string)
        miss_ratio = mismatching_bits / TOTAL_BITS
        score = round((1 - miss_ratio) * 100, 2)
        if score >= min_score:
            data = {
                'post_id': image_match.post_id,
                'score': score,
            }
            found_results.append(data)
    return sorted(found_results, key=lambda x: x['score'], reverse=True)
