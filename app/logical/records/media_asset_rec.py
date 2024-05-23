# APP/LOGICAL/RECORDS/MEDIA_ASSET_REC.PY

# ## PACKAGE IMPORTS
from utility.file import delete_file

# ### PACKAGE IMPORTS
from config import DELETE_MEDIA_ASSETS_PAGE_LIMIT, DELETE_MEDIA_ASSETS_PER_PAGE

# ## LOCAL IMPORTS
from ...models import MediaAsset
from ..database.media_asset_db import media_assets_without_media_models_query


# ## FUNCTIONS

def download_media_asset(download_url, source, location, alternate_url=None, override=True):
    results = {'media_asset': None, 'errors': []}
    download_url = illust_url.full_original_url
    file_ext = _get_media_extension(download_url, source)
    if isinstance(file_ext, tuple):
        results['errors'].append(file_ext)
        return results
    buffer = _download_media(download_url, source)
    if isinstance(buffer, tuple):
        results['errors'].append(buffer)
        if alternate_url is None:
            return results
        buffer = _download_media(alternate_url, source)
        if isinstance(buffer, tuple):
            results['errors'].append(buffer)
            return results
    media_asset = _check_existing(buffer, illust_url)
    if not isinstance(media_asset, str):
        if media_asset.location is not None or not override:
            return media_asset
        md5 = media_asset.md5
    else:
        md5 = media_asset
        media_asset = None
    media_file_ext = _check_filetype(buffer, file_ext, errors)
    if media_file_ext in ['jpg', 'png', 'gif']:
        image = _load_media_image(buffer)
        if image.is_animated:
            # Animated GIFs not handled yet.
            errors.append(('media_asset_rec.download_media_asset', "Animated GIFs are not supported."))
            return errors
        pixel_md5 = _get_pixel_hash(image)
        params = {
            'md5': md5,
            'width': image.width,
            'height': image.height,
            'size': len(buffer),
            'pixel_md5': pixel_md5,
            'file_ext': file_ext,
            'location': location,
        }
    if media_asset is None:
        media_asset = create_media_asset_from_parameters(params)
    else:
        media_asset = update_media_asset_from_parameters(media_asset, params)
    ret = create_data(buffer, media_asset.original_file_path)
    if ret is not None:
        results['errors'].append(('media.create_data', ret))
        update_media_asset_from_parameters(media_asset, {'location': None})
    return results


def delete_files_without_media_models(manual):
    """Delete media from assets not attached to posts, media files, or archives"""
    delete_count = 0
    max_pages = DELETE_MEDIA_ASSETS_PAGE_LIMIT if not manual else float('inf')
    q = media_assets_without_media_models_query()
    q = q.order_by(MediaAsset.id.desc())
    page = q.limit_paginate(per_page=DELETE_MEDIA_ASSETS_PER_PAGE)
    while True:
        print(f"delete_files_without_media_models: {page.first} - {page.last} / Total({page.count})\n")
        for media_asset in page.items:
            if not media_asset.has_file_access:
                continue
            delete_file(media_asset.original_file_path)
            delete_file(media_asset.image_sample_path)
            delete_file(media_asset.image_preview_path)
            if media_asset.is_video:
                delete_file(media_asset.video_sample_path)
                delete_file(media_asset.video_preview_path)
            delete_count += 0
        if not page.has_next or page.page >= max_pages:
            break
        page = page.next()
    return delete_count


# #### Private functions

def _check_existing(buffer, illust_url, record):
    md5 = get_buffer_checksum(buffer)
    media_asset = get_media_asset_by_md5(md5)
    return media_asset if media_asset is not None else md5
    if media_asset is not None:
        return media_asset
        update_illust_url_from_parameters(illust_url, {'post_id': post.id})
        if record.model_name == 'upload_element':
            update_upload_element_from_parameters(record, {'status': 'duplicate', 'media_asset_id': post.media_asset_id})
            if post.type.name != 'user':
                update_post_from_parameters(post, {'type': 'user'})
        elif record.model_name == 'subscription_element':
            duplicate_subscription_post(record, post.media_asset_id)
        elif record.model_name == 'upload':
            update_upload_from_parameters(record, {'status': 'duplicate'})
    if record.model_name == 'subscription_element' and record.status_name != 'deleted':
        elements = get_elements_by_md5(md5)
        if len(elements):
            duplicate_subscription_post(record, elements[0].media_asset_id)
            return None
    return md5


def _get_media_extension(original_url, source):
    file_ext = source.get_media_extension(original_url)
    if file_ext not in ['jpg', 'png', 'gif', 'mp4']:
        return ('media_asset_rec.get_media_extension', "Unsupported file format: %s" % file_ext)
    else:
        return file_ext


def _check_filetype(buffer, file_ext, errors):
    try:
        guess = filetype.guess(buffer)
    except Exception as e:
        errors.append(('media_asset_rec.check_filetype', "Error reading file headers: %s" % repr(e)))
        return file_ext
    if guess and guess.extension != file_ext:
        msg = "Mismatching file extensions: Reported - %s, Actual - %s" % (file_ext, guess.extension)
        errors.append(('media_asset_rec.check_filetype', msg))
        file_ext = guess.extension
    return file_ext


def _load_media_image(buffer):
    image = load_image(buffer)
    if isinstance(image, str):
        return ('media_rec.load_media_image', image)
    try:
        if check_alpha(image):
            return convert_alpha(image)
        else:
            return image
    except Exception as e:
        return create_error('media_rec.load_media_image', "Error removing alpha transparency: %s" % repr(e))


def _check_image_dimensions(image, illust_url, errors):
    if (illust_url.width and image.width != illust_url.width) or\
       (illust_url.height and image.height != illust_url.height):
        msg = "Mismatching image dimensions: Reported - %d x %d, Actual - %d x %d" %\
              (illust_url.width, illust_url.height, image.width, image.height)
        create_post_error('save_image', msg, post_errors)
    return image.width, image.height


def _download_media(download_url, source):
    print("Downloading", download_url)
    buffer = get_http_data(download_url, headers=source.IMAGE_HEADERS)
    if isinstance(buffer, str):
        return ('media_asset_rec.download_media', "Download URL: %s => %s" % (download_url, buffer))
    return buffer
