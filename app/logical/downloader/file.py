# APP/LOGICAL/DOWNLOADER/FILE.PY

# ## PACKAGE IMPORTS
from utility.file import get_file_extension, put_get_raw

# ## LOCAL IMPORTS
from ...models import Post
from ..media import get_pixel_hash
from ..database.post_db import create_post_and_add_illust_url
from ..database.error_db import create_and_append_error, extend_errors, is_error
from .base import convert_image_upload, convert_video_upload, load_post_image, check_existing, check_filetype,\
    check_image_dimensions, check_video_dimensions, save_image, save_video, save_thumb


# ## FUNCTIONS

def convert_file_upload(upload, source):
    illust_url = upload.illust_url
    illust = illust_url.illust
    if source.illust_has_videos(illust):
        if upload.sample_filepath is None:
            msg = "Must include sample filepath on video uploads (illust #%d)." % illust.id
            create_and_append_error('logical.downloader.file.convert_file_upload', msg, upload)
        else:
            return convert_video_upload(illust, upload, source, create_video_post, 'user_post')
    elif source.illust_has_images(illust):
        return convert_image_upload([illust_url], upload, source, create_image_post, 'user_post')
    create_and_append_error('logical.downloader.file.convert_file_upload', "No valid illust URLs.", upload)
    return False

# #### Post creation functions


def create_image_post(illust_url, record, source, post_type):
    file_ext = get_file_extension(record.media_filepath)
    buffer = put_get_raw(record.media_filepath, 'rb')
    md5 = check_existing(buffer, illust_url, record)
    if is_error(md5):
        return [md5]
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
    post = create_post_and_add_illust_url(illust_url, image_width, image_height, image_file_ext, md5, len(buffer),
                                          post_type, pixel_md5)
    if len(post_errors):
        extend_errors(post, post_errors)
    return post


def create_video_post(illust_url, upload, source):
    file_ext = get_file_extension(upload.media_filepath)
    buffer = put_get_raw(upload.media_filepath, 'rb')
    md5 = check_existing(buffer, illust_url)
    if is_error(md5):
        return [md5]
    post_errors = []
    video_file_ext = check_filetype(buffer, file_ext, post_errors)
    temppost = Post(md5=md5, file_ext=video_file_ext)
    error = save_video(buffer, temppost)
    if error is not None:
        return post_errors + [error]
    video_width, video_height = check_video_dimensions(temppost, illust_url, post_errors)
    thumb_binary = put_get_raw(upload.sample_filepath, 'rb')
    save_thumb(thumb_binary, temppost, post_errors)
    post = create_post_and_add_illust_url(illust_url, video_width, video_height, video_file_ext, md5, len(buffer),
                                          None)
    if len(post_errors):
        extend_errors(post, post_errors)
    return post
