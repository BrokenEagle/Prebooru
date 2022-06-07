# APP/LOGICAL/DOWNLOADER/NETWORK.PY

# ## LOCAL IMPORTS
from ..network import get_http_file
from ...models import Post
from ..database.post_db import create_post_and_add_illust_url
from ..database.error_db import create_error, create_and_append_error, append_error, extend_errors, is_error
from .base import convert_image_upload, convert_video_upload, load_image, check_existing, check_filetype,\
    check_image_dimensions, check_video_dimensions, save_image, save_video, save_thumb


# ## FUNCTIONS

# #### Main execution functions

def convert_network_upload(illust, upload, source):
    if source.illust_has_videos(illust):
        return convert_video_upload(illust.urls[0], upload, source, create_video_post, 'user_post')
    elif source.illust_has_images(illust):
        all_upload_urls = [source.normalize_image_url(upload_url.url) for upload_url in upload.image_urls]
        image_illust_urls = [illust_url for illust_url in source.image_illust_download_urls(illust)
                             if (len(all_upload_urls) == 0) or (illust_url.url in all_upload_urls)]
        return convert_image_upload(image_illust_urls, upload, source, create_image_post, 'user_post')
    create_and_append_error('downloader.file.convert_network_upload', "No valid illust URLs.", upload)
    return False


def convert_network_subscription(subscription, source):
    illust = subscription.illust_url.illust
    if source.illust_has_videos(illust):
        return convert_video_upload(illust.urls[0], subscription, source, create_video_post, 'subscription_post')
    elif source.illust_has_images(illust):
        return convert_image_upload([subscription.illust_url], subscription, source, create_image_post,
                                    'subscription_post')
    create_and_append_error('downloader.file.convert_network_subscription', "No valid illust URLs.", subscription)
    return False


def redownload_post(post, illust_url, source):
    illust = illust_url.illust
    if source.illust_has_videos(illust):
        return convert_video_upload(illust, post, source, update_video_post, None)
    elif source.illust_has_images(illust):
        return convert_image_upload([illust_url], post, source, update_image_post, None)
    create_and_append_error('downloader.network.redownload_post', "No valid illust URLs.", post)
    return False


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
    download_url = source.get_full_url(illust_url) if not sample else source.get_sample_url(illust_url)
    buffer = _download_media(download_url, source)
    if not is_error(buffer):
        return buffer
    elif sample:
        return [buffer]
    error = buffer
    alternate_url = source.get_alternate_url(illust_url)
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
    if is_error(md5):
        return [md5]
    post_errors = []
    image_file_ext = check_filetype(buffer, file_ext, post_errors)
    image = load_image(buffer)
    if is_error(image):
        return post_errors + [image]
    image_width, image_height = check_image_dimensions(image, illust_url, post_errors)
    temppost = Post(md5=md5, file_ext=image_file_ext, width=image_width, height=image_height)
    if not save_image(buffer, image, temppost, post_errors):
        return post_errors
    post = create_post_and_add_illust_url(illust_url, image_width, image_height, image_file_ext, md5, len(buffer),
                                          post_type)
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
    if is_error(md5):
        return [md5]
    post_errors = []
    video_file_ext = check_filetype(buffer, file_ext, post_errors)
    temppost = Post(md5=md5, file_ext=video_file_ext)
    error = save_video(buffer, temppost)
    if error is not None:
        return post_errors + [error]
    video_width, video_height = check_video_dimensions(temppost, illust_url, post_errors)
    thumb_binary = download_media(illust_url, source, record, True)
    if isinstance(thumb_binary, list):
        return post_errors + thumb_binary
    save_thumb(thumb_binary, temppost, post_errors)
    post = create_post_and_add_illust_url(illust_url, video_width, video_height, video_file_ext, md5, len(buffer),
                                          post_type)
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
    image_file_ext = check_filetype(buffer, file_ext, post_errors)
    image = load_image(buffer)
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
    video_file_ext = check_filetype(buffer, file_ext, post_errors)
    error = save_video(buffer, post)
    if error is not None:
        return post_errors + [error]
    video_width, video_height = check_video_dimensions(post, illust_url, post_errors)
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
    buffer = get_http_file(download_url, headers=source.IMAGE_HEADERS)
    if isinstance(buffer, str):
        return create_error('downloader.network.download_media', "Download URL: %s => %s" % (download_url, buffer))
    return buffer
