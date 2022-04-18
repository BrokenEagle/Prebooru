# APP/LOGICAL/SIMILARITY/GENERATE_DATA.PY

# ## LOCAL IMPORTS
from ..database.similarity_data_db import create_similarity_data_from_parameters
from .base import get_image, get_image_hash, check_similarity_match_scores


# ## FUNCTIONS

def generate_post_similarity(post, printer=print):
    ratio = round(post.width / post.height, 4)
    params = {
        'post_id': post.id,
        'ratio': ratio,
    }
    preview_image = get_image(post.preview_path)
    preview_image_hash = get_image_hash(preview_image)
    printer("Generate similarity (post #%d): PREVIEW" % post.id)
    simdata_items = [create_similarity_data_from_parameters({'image_hash': preview_image_hash, **params})]
    if post.file_ext != 'mp4':
        full_image = get_image(post.file_path)
        full_image_hash = get_image_hash(full_image)
        if len(check_similarity_match_scores(simdata_items, full_image_hash, 90.0)) == 0:
            printer("Generate similarity (post #%d): FULL" % post.id)
            simdata_items.append(create_similarity_data_from_parameters({'image_hash': full_image_hash, **params}))
    if post.file_path != post.sample_path:
        sample_image = get_image(post.sample_path)
        sample_image_hash = get_image_hash(sample_image)
        if len(check_similarity_match_scores(simdata_items, sample_image_hash, 90.0)) == 0:
            printer("Generate similarity (post #%d): SAMPLE" % post.id)
            simdata_items.append(create_similarity_data_from_parameters({'image_hash': sample_image_hash, **params}))
    return simdata_items
