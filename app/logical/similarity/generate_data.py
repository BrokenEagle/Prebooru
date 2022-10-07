# APP/LOGICAL/SIMILARITY/GENERATE_DATA.PY

# ## LOCAL IMPORTS
from ..database.image_hash_db import create_image_hash_from_parameters
from .base import get_image, get_image_hash, check_image_match_scores


# ## FUNCTIONS

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
        imghash_items.append(create_image_hash_from_parameters({'hash': preview_image_hash, **params}))
    if post.file_ext != 'mp4':
        full_image = get_image(post.file_path)
        full_image_hash = get_image_hash(full_image)
        if len(imghash_items) == 0 or len(check_image_match_scores(imghash_items, full_image_hash, 90.0)) == 0:
            printer("Generate image hash (post #%d): FULL" % post.id)
            imghash_items.append(create_image_hash_from_parameters({'hash': full_image_hash, **params}))
    if post.has_sample:
        sample_image = get_image(post.sample_path)
        sample_image_hash = get_image_hash(sample_image)
        if len(imghash_items) == 0 or len(check_image_match_scores(imghash_items, sample_image_hash, 90.0)) == 0:
            printer("Generate image hash (post #%d): SAMPLE" % post.id)
            imghash_items.append(create_image_hash_from_parameters({'hash': sample_image_hash, **params}))
    return imghash_items
