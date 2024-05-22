# APP/LOGICAL/DOWNLOADER/FILE_DL.PY

# ## PACKAGE IMPORTS
from utility.file import get_file_extension, put_get_raw

# ## LOCAL IMPORTS
from ...models import Post
from ..media import get_pixel_hash
from ..records.post_rec import create_post_record
from ..database.error_db import extend_errors, is_error
from .base_dl import load_post_image, check_existing, check_filetype, check_image_dimensions,\
    check_video_info, save_image, save_video, save_thumb, record_outcome


# ## FUNCTIONS

def convert_file_upload(upload):
    if upload.file_illust_url.type == 'image':
        result = create_image_post(upload, 'user')
    elif upload.file_illust_url.type == 'video':
        result = create_video_post(upload, 'user')
    return record_outcome(result, upload)


# #### Post creation functions

def create_image_post(record, post_type):
    illust_url = record.file_illust_url
    file_ext = get_file_extension(record.media_filepath)
    buffer = put_get_raw(record.media_filepath, 'rb')
    md5 = check_existing(buffer, illust_url, record)
    if md5 is None:
        return None
    post_errors = []
    image_file_ext = check_filetype(buffer, file_ext, post_errors)
    image = load_post_image(buffer)
    if is_error(image):
        return post_errors + [image]
    image_width, image_height = check_image_dimensions(image, illust_url, post_errors)
    temppost = Post(md5=md5, file_ext=image_file_ext, width=image_width, height=image_height)
    if not save_image(buffer, image, temppost, post_errors):
        return post_errors
    pixel_md5 = get_pixel_hash(image)
    post = create_post_record(illust_url, image_width, image_height, image_file_ext, md5, len(buffer), post_type,
                              pixel_md5, None, None)
    if len(post_errors):
        extend_errors(post, post_errors)
    return post


def create_video_post(record, post_type):
    illust_url = record.file_illust_url
    file_ext = get_file_extension(record.media_filepath)
    buffer = put_get_raw(record.media_filepath, 'rb')
    md5 = check_existing(buffer, illust_url)
    if md5 is None:
        return None
    post_errors = []
    video_file_ext = check_filetype(buffer, file_ext, post_errors)
    temppost = Post(md5=md5, file_ext=video_file_ext)
    error = save_video(buffer, temppost)
    if error is not None:
        return post_errors + [error]
    vinfo = check_video_info(temppost, illust_url, post_errors)
    thumb_binary = put_get_raw(record.sample_filepath, 'rb')
    save_thumb(thumb_binary, temppost, post_errors)
    post = create_post_record(illust_url, vinfo['width'], vinfo['height'], video_file_ext, md5, len(buffer), post_type,
                              None, vinfo['duration'], vinfo['audio'])
    if len(post_errors):
        extend_errors(post, post_errors)
    return post
