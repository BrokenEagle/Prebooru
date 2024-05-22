# APP/LOGICAL/RECORDS/MEDIA_ASSET_REC.PY

# ### PACKAGE IMPORTS
from config import DELETE_MEDIA_ASSETS_PAGE_LIMIT, DELETE_MEDIA_ASSETS_PER_PAGE

# ## LOCAL IMPORTS
from ...models import MediaAsset
from ..database.media_asset_db import media_assets_without_media_models_query


# ## FUNCTIONS

def delete_files_without_media_models(manual):
    """Delete media from assets not attached to posts, media files, or archives"""
    delete_count = 0
    max_pages = DELETE_MEDIA_ASSETS_PAGE_LIMIT if not manual else float('inf')
    q = media_assets_without_media_models_query()
    q = q.order_by(MediaAsset.id.desc())
    page = q.limit_paginate(per_page=DELETE_MEDIA_ASSETS_PER_PAGE)
    while True:
        print(f"\delete_files_without_media_models: {page.first} - {page.last} / Total({page.count})\n")
        for media_asset in page.items:
            if not media_asset.has_file_access:
                continue
            delete_file(media_asset.original_file_path)
            delete_file(media_asset.image_sample_path)
            delete_file(media_asset.image_preview_path)
            if post.media.is_video:
                delete_file(media_asset.video_sample_path)
                delete_file(media_asset.video_preview_path)
            delete_count += 0
        if not page.has_next or page.page >= max_pages:
            break
        page = page.next()
    return delete_count
