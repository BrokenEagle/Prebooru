# APP/LOGICAL/RECORDS/MEDIA_ASSET_REC.PY

# ## PYTHON IMPORTS
import os
import filetype

# ## PACKAGE IMPORTS
from utility.data import merge_dicts
from utility.file import copy_file, delete_file

# ### PACKAGE IMPORTS
from config import DELETE_MEDIA_ASSETS_PAGE_LIMIT, DELETE_MEDIA_ASSETS_PER_PAGE, TEMP_DIRECTORY
from utility.data import get_buffer_checksum

# ## LOCAL IMPORTS
from ...models import MediaAsset
from ..network import get_http_data
from ..media import create_data, load_image, get_pixel_hash, get_duration, get_video_info
from ..database.media_asset_db import create_media_asset_from_parameters, update_media_asset_from_parameters,\
    media_assets_without_media_models_query, get_media_asset_by_md5
from ..database.error_db import create_error


# ## FUNCTIONS

def download_media_asset(download_url, source, location, alternate_url=None):
    errors = []
    results = {'media_asset': None, 'errors': errors, 'duplicate': False}
    file_ext = _get_media_extension(download_url, source)
    if isinstance(file_ext, tuple):
        errors.append(file_ext)
        return results
    buffer = _download_media(download_url, source)
    if isinstance(buffer, tuple):
        errors.append(buffer)
        if alternate_url is None:
            return results
        buffer = _download_media(alternate_url, source)
        if isinstance(buffer, tuple):
            errors.append(buffer)
            return results
    media_asset = _check_existing(buffer)
    if not isinstance(media_asset, str):
        if media_asset.location is not None:
            results['media_asset'] = media_asset
            results['duplicate'] = True
            return results
        md5 = media_asset.md5
    else:
        md5 = media_asset
        media_asset = None
    media_file_ext = _check_filetype(buffer, file_ext, errors)
    if media_file_ext in ['jpg', 'png', 'gif']:
        info = get_media_image_info(buffer, media_file_ext, errors)
    elif media_file_ext == 'mp4':
        info = get_media_video_info(buffer, md5, errors)
    else:
        info = None
        errors.append(('media_asset_rec.download_media_asset', "Unhandled file extension: %s" % media_file_ext))
    if info is None:
        return results
    params = merge_dicts(info, {
        'md5': md5,
        'size': len(buffer),
        'file_ext': file_ext,
        'location': location,
    })
    if media_asset is None:
        media_asset = create_media_asset_from_parameters(params)
    else:
        media_asset = update_media_asset_from_parameters(media_asset, params)
    results['media_asset'] = media_asset
    ret = create_data(buffer, media_asset.original_file_path)
    if ret is not None:
        errors.append(('media.create_data', ret))
        update_media_asset_from_parameters(media_asset, {'location': None})
    return results


def get_media_image_info(buffer, media_file_ext, errors):
    image = load_image(buffer)
    if isinstance(image, str):
        errors.append(('media_asset_rec.get_media_image_info', image))
        return
    info = {
        'width': image.width,
        'height': image.height,
    }
    duration = get_duration(image) if media_file_ext == 'gif' else 0
    if duration == 0:
        info['pixel_md5'] = get_pixel_hash(image)
    else:
        info['duration'] = duration
    return info


def get_media_video_info(buffer, md5, errors):
    temp_path = os.path.join(TEMP_DIRECTORY, md5 + '.' + 'mp4')
    ret = create_data(buffer, temp_path)
    if ret is not None:
        errors.append(('media_asset_rec.get_media_video_info', "Unable to save video to temp directory"))
        return
    info = get_video_info(temp_path)
    delete_file(temp_path)
    if isinstance(info, str):
        errors.append(('media_asset_rec.get_media_video_info', "Unable to save video to temp directory"))
        return
    return info


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


def move_media_asset(media_asset, location):
    if location == 'alternate' or media_asset.location.name == 'alternate':
        if not MediaAsset.alternate_location_configured():
            return "Alternate location not configured"
        if not MediaAsset.alternate_location_available():
            return "Alternate location not available"
    move_asset = media_asset.copy()
    move_asset.location = media_asset.location_enum.by_name(location)
    copy_file(media_asset.original_file_path, move_asset.original_file_path, safe=True)
    move_asset.location = media_asset.location
    update_media_asset_from_parameters(media_asset, {'location': location})
    delete_file(move_asset.original_file_path)


# #### Private functions

def _check_existing(buffer):
    md5 = get_buffer_checksum(buffer)
    media_asset = get_media_asset_by_md5(md5)
    return media_asset if media_asset is not None else md5


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


def _check_image_dimensions(image, illust_url, errors):
    if (illust_url.width and image.width != illust_url.width) or\
       (illust_url.height and image.height != illust_url.height):
        message = "Mismatching image dimensions: Reported - %d x %d, Actual - %d x %d" %\
                  (illust_url.width, illust_url.height, image.width, image.height)
        error = create_error('media_rec.check_image_dimensions', message)
        errors.append(error)
    return image.width, image.height


def _download_media(download_url, source):
    print("Downloading", download_url)
    buffer = get_http_data(download_url, headers=source.IMAGE_HEADERS)
    if isinstance(buffer, str):
        return ('media_asset_rec.download_media', "Download URL: %s => %s" % (download_url, buffer))
    return buffer
