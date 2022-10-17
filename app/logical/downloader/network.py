# APP/LOGICAL/DOWNLOADER/NETWORK.PY

# ## LOCAL IMPORTS
from ..network import get_http_data
from ..media import get_pixel_hash
from ...models import Post
from ..database.post_db import create_post_and_add_illust_url, update_post_from_parameters
from ..database.error_db import create_error, append_error, extend_errors, is_error
from .base import convert_media_upload, load_post_image, check_existing, check_filetype, check_image_dimensions,\
    check_video_info, save_image, save_video, save_thumb


# ## FUNCTIONS

# #### Main execution functions

def convert_network_upload(upload_element, source):
    return convert_media_upload([upload_element.illust_url], upload_element, source,
                                create_image_post, create_video_post, 'user')


def convert_network_subscription(subscription, source):
    return convert_media_upload([subscription.illust_url], subscription, source,
                                create_image_post, create_video_post, 'subscription')


def redownload_post(post, illust_url, source):
    return convert_media_upload(illust_url, post, source, create_image_post, create_video_post, None)


# #### Auxiliary functions

def get_media_extension(illust_url, source):
    full_url = source.get_full_url(illust_url)
    file_ext = source.get_media_extension(full_url)
    if file_ext not in ['jpg', 'png', 'mp4']:
        return create_error('downloader.network.get_media_extension', "Unsupported file format: %s" % file_ext)
    else:
        return file_ext


# #### Network functions

def download_media(illust_url, source, record, sample):
    download_url = source.get_full_url(illust_url) if not sample else source.get_sample_url(illust_url, True)
    buffer = _download_media(download_url, source)
    if not is_error(buffer):
        return buffer
    elif sample:
        return [buffer]
    error = buffer
    alternate_url = source.get_alternate_url(illust_url) if not sample else source.get_sample_url(illust_url, False)
    if alternate_url is None:
        return [error]
    buffer = _download_media(alternate_url, source)
    if is_error(buffer):
        return [error, buffer]
    append_error(record, error)
    return buffer


# #### Post creation functions

def create_image_post(illust_url, record, source, post_type):
    file_ext = get_media_extension(illust_url, source)
    if is_error(file_ext):
        return [file_ext]
    buffer = download_media(illust_url, source, record, False)
    if isinstance(buffer, list):
        return buffer
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
    post = create_post_and_add_illust_url(illust_url, image_width, image_height, image_file_ext, md5, len(buffer),
                                          post_type, pixel_md5, None, None)
    if len(post_errors):
        extend_errors(post, post_errors)
    return post


def create_video_post(illust_url, record, source, post_type):
    file_ext = get_media_extension(illust_url, source)
    if is_error(file_ext):
        return [file_ext]
    buffer = download_media(illust_url, source, record, False)
    if isinstance(buffer, list):
        return buffer
    md5 = check_existing(buffer, illust_url, record)
    if md5 is None:
        return None
    post_errors = []
    video_file_ext = check_filetype(buffer, file_ext, post_errors)
    temppost = Post(md5=md5, file_ext=video_file_ext)
    error = save_video(buffer, temppost)
    if error is not None:
        return post_errors + [error]
    vinfo = check_video_info(temppost, illust_url, post_errors)
    thumb_binary = download_media(illust_url, source, record, True)
    if isinstance(thumb_binary, list):
        return post_errors + thumb_binary
    save_thumb(thumb_binary, temppost, post_errors)
    post = create_post_and_add_illust_url(illust_url, vinfo['width'], vinfo['height'], video_file_ext, md5, len(buffer),
                                          post_type, None, vinfo['duration'], vinfo['audio'])
    if len(post_errors):
        extend_errors(post, post_errors)
    return post


# #### Post update functions

def update_image_post(illust_url, post, source, *args):
    file_ext = get_media_extension(illust_url, source)
    if is_error(file_ext):
        return [file_ext]
    buffer = download_media(illust_url, source, post, False)
    if isinstance(buffer, list):
        return buffer
    post_errors = []
    check_filetype(buffer, file_ext, post_errors)
    image = load_post_image(buffer)
    if is_error(image):
        return post_errors + [image]
    image_width, image_height = check_image_dimensions(image, illust_url, post_errors)
    if not save_image(buffer, image, post, post_errors):
        return post_errors
    if len(post_errors):
        extend_errors(post, post_errors)
    return post


def update_video_post(illust_url, post, source, *args):
    file_ext = get_media_extension(illust_url, source)
    if is_error(file_ext):
        return [file_ext]
    buffer = download_media(illust_url, source, post, False)
    if isinstance(buffer, list):
        return buffer
    post_errors = []
    check_filetype(buffer, file_ext, post_errors)
    error = save_video(buffer, post)
    if error is not None:
        return post_errors + [error]
    vinfo = check_video_info(post, illust_url, post_errors)
    update_post_from_parameters(post, vinfo)
    thumb_binary = download_media(illust_url, source, post, True)
    if isinstance(thumb_binary, list):
        return post_errors + thumb_binary
    save_thumb(thumb_binary, post, post_errors)
    if len(post_errors):
        extend_errors(post, post_errors)
    return post


# #### Private functions

def _download_media(download_url, source):
    print("Downloading", download_url)
    buffer = get_http_data(download_url, headers=source.IMAGE_HEADERS)
    if isinstance(buffer, str):
        return create_error('downloader.network.download_media', "Download URL: %s => %s" % (download_url, buffer))
    return buffer
