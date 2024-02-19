# APP/LOGICAL/RECORDS/IMAGE_HASH_REC.PY

# ## PYTHON IMPORTS
from PIL import Image

# ## EXTERNAL IMPORTS
import distance
import imagehash

# ## LOCAL IMPORTS
from ...models.image_hash import ImageHash, HASH_SIZE, TOTAL_BITS
from ..sources.base_src import get_media_source, NoSource
from ..database.post_db import get_posts_by_id
from ..database.image_hash_db import create_image_hash_from_parameters
from .media_file_rec import batch_get_or_create_media


# ## FUNCTIONS

# #### Helper functions

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


# #### Auxiliary functions

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


def check_media_file_image_matches(media_file, min_score, limit, include_posts=False, sim_clause=None):
    if type(media_file) is str:
        return media_file
    image = get_image(media_file.file_path)
    image_hash = get_image_hash(image)
    ratio = round(image.width / image.height, 4)
    imghash_matches = get_image_hash_matches(image_hash, ratio, sim_clause=sim_clause)
    score_results = check_image_match_scores(imghash_matches, image_hash, min_score)
    final_results = filter_score_results(score_results)
    if len(final_results) > limit:
        final_results = final_results[:limit]
    if include_posts:
        post_ids = [result['post_id'] for result in final_results]
        posts = get_posts_by_id(post_ids)
        for result in final_results:
            post = next(filter(lambda x: x.id == result['post_id'], posts), None)
            result['post'] = post.to_json() if post is not None else post
    return final_results


# #### Main execution functions

def generate_post_image_hashes(post, printer=print):
    ratio = round(post.width / post.height, 4)
    params = {
        'post_id': post.id,
        'ratio': ratio,
    }
    imghash_items = []
    if post.has_preview:
        preview_image = get_image(post.preview_path)
        preview_image_hash = get_image_hash(preview_image)
        printer("Generate image hash (post #%d): PREVIEW" % post.id)
        imghash_items.append(create_image_hash_from_parameters({'hash': preview_image_hash, **params}, True))
    if post.file_ext != 'mp4':
        full_image = get_image(post.file_path)
        full_image_hash = get_image_hash(full_image)
        if len(imghash_items) == 0 or len(check_image_match_scores(imghash_items, full_image_hash, 90.0)) == 0:
            printer("Generate image hash (post #%d): FULL" % post.id)
            imghash_items.append(create_image_hash_from_parameters({'hash': full_image_hash, **params}, True))
    if post.has_sample:
        sample_image = get_image(post.sample_path)
        sample_image_hash = get_image_hash(sample_image)
        if len(imghash_items) == 0 or len(check_image_match_scores(imghash_items, sample_image_hash, 90.0)) == 0:
            printer("Generate image hash (post #%d): SAMPLE" % post.id)
            imghash_items.append(create_image_hash_from_parameters({'hash': sample_image_hash, **params}, True))
    return imghash_items


def check_all_image_urls_for_matches(image_urls, min_score, size, limit, include_posts=False, sim_clause=None):
    media_sources = [get_media_source(image_url) or NoSource() for image_url in image_urls]
    if size == 'actual':
        download_urls = image_urls
    elif size == 'original':
        download_urls = [source.original_image_url(image_urls[i]) for (i, source) in enumerate(media_sources)]
    elif size == 'small':
        download_urls = [source.small_image_url(image_urls[i]) for (i, source) in enumerate(media_sources)]
    normalized_urls = [source.normalized_image_url(image_urls[i]) for (i, source) in enumerate(media_sources)]
    media_batches = list(zip(download_urls, media_sources))
    media_files = batch_get_or_create_media(media_batches)
    post_results = []
    for media in media_files:
        if isinstance(media, str):
            post_results.append(None)
        else:
            result = check_media_file_image_matches(media, min_score, limit, include_posts=include_posts,
                                                    sim_clause=sim_clause)
            post_results.append(result)
    image_match_results = []
    for i in range(len(image_urls)):
        is_error = isinstance(media_files[i], str)
        image_match_result =\
            {
                'image_url': normalized_urls[i],
                'download_url': download_urls[i],
                'post_results': post_results[i],
                'media_file': media_files[i] if not is_error else None,
                'error': is_error,
                'message': media_files[i] if is_error else None,
            }
        image_match_results.append(image_match_result)
    return image_match_results
