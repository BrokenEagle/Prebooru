# APP/LOGICAL/SIMILARITY/CHECK_IMAGE.PY

# ## LOCAL IMPORTS
from ..database.post_db import get_posts_by_id
from ..sources.base import get_media_source, NoSource
from ..records.media_file_rec import batch_get_or_create_media
from .base import get_image, get_image_hash, get_image_hash_matches, check_image_match_scores,\
    filter_score_results


# ## FUNCTIONS

def check_all_image_urls_for_matches(image_urls, min_score, size, include_posts=False, sim_clause=None):
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
            result = check_media_file_image_matches(media, min_score, include_posts=include_posts,
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


def check_media_file_image_matches(media_file, min_score, include_posts=False, sim_clause=None):
    if type(media_file) is str:
        return media_file
    image = get_image(media_file.file_path)
    image_hash = get_image_hash(image)
    ratio = round(image.width / image.height, 4)
    imghash_matches = get_image_hash_matches(image_hash, ratio, sim_clause=sim_clause)
    score_results = check_image_match_scores(imghash_matches, image_hash, min_score)
    final_results = filter_score_results(score_results)
    if include_posts:
        post_ids = [result['post_id'] for result in final_results]
        posts = get_posts_by_id(post_ids)
        for result in final_results:
            post = next(filter(lambda x: x.id == result['post_id'], posts), None)
            result['post'] = post.to_json() if post is not None else post
    return final_results
