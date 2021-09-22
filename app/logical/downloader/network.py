# APP/LOGICAL/DOWNLOADER/NETWORK.PY

# ## LOCAL IMPORTS
from ..network import get_http_file
from ...models import Post
from ...database.post_db import create_post_and_add_illust_url
from ...database.error_db import create_error, create_and_append_error, extend_errors, is_error
from .base import convert_image_upload, convert_video_upload, load_image, check_existing, check_filetype,\
    check_image_dimensions, check_video_dimensions, save_image, save_video, save_thumb


# ## FUNCTIONS

# #### Main execution functions

def convert_network_upload(illust, upload, source):
    if source.illust_has_videos(illust):
        return convert_video_upload(illust, upload, source, create_video_post)
    elif source.illust_has_images(illust):
        all_upload_urls = [source.normalize_image_url(upload_url.url) for upload_url in upload.image_urls]
        image_illust_urls = [illust_url for illust_url in source.image_illust_download_urls(illust)
                             if (len(all_upload_urls) == 0) or (illust_url.url in all_upload_urls)]
        return convert_image_upload(image_illust_urls, upload, source, create_image_post)
    create_and_append_error('logical.downloader.file.convert_network_upload', "No valid illust URLs.", upload)
    return False


# #### Network functions

def download_media(illust_url, source):
    download_url = source.get_full_url(illust_url)
    file_ext = source.get_media_extension(download_url)
    if file_ext not in ['jpg', 'png', 'mp4']:
        return create_error('logical.downloader.network.download_media', "Unsupported file format: %s" % file_ext), None
    print("Downloading", download_url)
    buffer = get_http_file(download_url, headers=source.IMAGE_HEADERS)
    if type(buffer) is str:
        return create_error('logical.downloader.network.download_media', buffer), None
    return buffer, file_ext


# #### Post creation functions

def create_image_post(image_illust_url, upload, source):
    buffer, file_ext = download_media(image_illust_url, source)
    if is_error(buffer):
        return [buffer]
    md5 = check_existing(buffer, image_illust_url)
    if is_error(md5):
        return [md5]
    post_errors = []
    image_file_ext = check_filetype(buffer, file_ext, post_errors)
    image = load_image(buffer)
    if is_error(image):
        return post_errors + [image]
    image_width, image_height = check_image_dimensions(image, image_illust_url, post_errors)
    temppost = Post(md5=md5, file_ext=image_file_ext, width=image_width, height=image_height)
    if not save_image(buffer, image, temppost, post_errors):
        return post_errors
    post = create_post_and_add_illust_url(image_illust_url, image_width, image_height, image_file_ext, md5, len(buffer))
    if len(post_errors):
        extend_errors(post, post_errors)
    return post


def create_video_post(video_illust_url, thumb_illust_url, upload, source):
    buffer, file_ext = download_media(video_illust_url, source)
    if is_error(buffer):
        return [buffer]
    md5 = check_existing(buffer, video_illust_url)
    if is_error(md5):
        return [md5]
    post_errors = []
    video_file_ext = check_filetype(buffer, file_ext, post_errors)
    temppost = Post(md5=md5, file_ext=video_file_ext)
    error = save_video(buffer, md5, video_file_ext)
    if error is not None:
        return post_errors + [error]
    video_width, video_height = check_video_dimensions(temppost, video_illust_url, post_errors)
    thumb_binary, _ = download_media(thumb_illust_url, source)
    if is_error(thumb_binary):
        return post_errors + [thumb_binary]
    save_thumb(thumb_binary, temppost, post_errors)
    post = create_post_and_add_illust_url(video_illust_url, video_width, video_height, video_file_ext, md5, len(buffer))
    if len(post_errors):
        extend_errors(post, post_errors)
    return post
