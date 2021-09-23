# APP\LOGICAL\SIMILARITY\CHECK_IMAGE.PY

# ## LOCAL IMPORTS
from ...database.post_db import get_posts_by_id
from ...sources.base_source import get_image_source, NoSource
from .base import get_or_create_media, get_image, get_image_hash, get_similarity_data_matches, check_similarity_match_scores,\
    filter_score_results


# ## FUNCTIONS

def check_all_image_urls_similarity(image_urls, min_score, use_original=False, include_posts=False):
    similar_results = []
    for image_url in image_urls:
        similar_result = check_image_url_similarity(image_url, min_score, use_original, include_posts)
        similar_results.append(similar_result)
    return similar_results


def check_image_url_similarity(image_url, min_score, use_original=False, include_posts=False):
    source = get_image_source(image_url) or NoSource()
    download_url = source.small_image_url(image_url) if not use_original else image_url
    media_file = get_or_create_media(download_url, source)
    if type(media_file) is str:
        return media_file
    image = get_image(media_file.file_path)
    image_hash = get_image_hash(image)
    ratio = round(image.width / image.height, 4)
    simdata_matches = get_similarity_data_matches(image_hash, ratio)
    score_results = check_similarity_match_scores(simdata_matches, image_hash, min_score)
    final_results = filter_score_results(score_results)
    if include_posts:
        post_ids = [result['post_id'] for result in final_results]
        posts = get_posts_by_id(post_ids)
        for result in final_results:
            post = next(filter(lambda x: x.id == result['post_id'], posts), None)
            result['post'] = post.to_json() if post is not None else post
    normalized_url = source.normalized_image_url(image_url) if not use_original else image_url
    return {'image_url': normalized_url, 'post_results': final_results, 'cache': media_file.file_url}
