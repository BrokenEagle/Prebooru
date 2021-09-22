# APP/LOGICAL/DOWNLOADER/BASE.PY

# ## PYTHON IMPORTS
import ffmpeg
import filetype
from PIL import Image
from io import BytesIO

# ## LOCAL IMPORTS
from ..utility import get_buffer_checksum
from ..file import create_directory, put_get_raw
from ...config import PREVIEW_DIMENSIONS, SAMPLE_DIMENSIONS
from ...database.upload_db import add_upload_success, add_upload_failure, upload_append_post
from ...database.post_db import post_append_illust_url, get_post_by_md5
from ...database.error_db import create_error, create_and_append_error, extend_errors, is_error


# ## FUNCTIONS

# #### Main execution functions

def convert_video_upload(illust, upload, source, create_video_func):
    video_illust_url, thumb_illust_url = source.VideoIllustDownloadUrls(illust)
    if thumb_illust_url is None:
        create_and_append_error('logical.downloader.convert_video_upload', "Did not find thumbnail for video on illust #%d" % illust.id, upload)
        return False
    else:
        post = create_video_func(video_illust_url, thumb_illust_url, upload, source)
        return record_outcome(post, upload)


def convert_image_upload(illust_urls, upload, source, create_image_func):
    result = False
    for illust_url in illust_urls:
        post = create_image_func(illust_url, upload, source)
        result = record_outcome(post, upload) or result
    return result


# #### Helper functions

def record_outcome(post, upload):
    if isinstance(post, list):
        post_errors = post
        valid_errors = [error for error in post_errors if is_error(error)]
        if len(valid_errors) != len(post_errors):
            print("\aInvalid data returned in outcome:", [item for item in post_errors if not is_error(item)])
        extend_errors(upload, valid_errors)
        add_upload_failure(upload)
        return False
    else:
        upload_append_post(upload, post)
        add_upload_success(upload)
        return True


def load_image(buffer):
    try:
        file_imgdata = BytesIO(buffer)
        image = Image.open(file_imgdata)
    except Exception as e:
        return create_error('logical.downloader.base.load_image', "Error processing image data: %s" % repr(e))
    return image


def create_post_error(module, message, post_errors):
    error = create_error(module, message)
    post_errors.append(error)


# #### Validation functions

def check_existing(buffer, illust_url):
    md5 = get_buffer_checksum(buffer)
    post = get_post_by_md5(md5)
    if post is not None:
        post_append_illust_url(post, illust_url)
        return create_error('logical.downloader.base.check_existing', "Image already uploaded on post #%d" % post.id)
    return md5


def check_filetype(buffer, file_ext, post_errors):
    try:
        guess = filetype.guess(buffer)
    except Exception as e:
        create_post_error('logical.downloader.base.check_filetype', "Error reading file headers: %s" % repr(e), post_errors)
        return file_ext
    if guess.extension != file_ext:
        create_post_error('logical.downloader.base.check_filetype', "Mismatching file extensions: Reported - %s, Actual - %s" % (file_ext, guess.extension), post_errors)
        file_ext = guess.extension
    return file_ext


def check_image_dimensions(image, image_illust_url, post_errors):
    if (image_illust_url.width and image.width != image_illust_url.width) or (image_illust_url.height and image.height != image_illust_url.height):
        create_post_error('logical.downloader.base.save_image', "Mismatching image dimensions: Reported - %d x %d, Actual - %d x %d" % (image_illust_url.width, image_illust_url.height, image.width, image.height), post_errors)
    return image.width, image.height


def check_video_dimensions(post, video_illust_url, post_errors):
    try:
        probe = ffmpeg.probe(post.file_path)
    except FileNotFoundError:
        create_post_error('logical.downloader.base.check_video_dimensions', "Must install ffprobe.exe. See Github page for details.", post_errors)
        return video_illust_url.width, video_illust_url.height
    except Exception as e:
        create_post_error('logical.downloader.base.check_video_dimensions', "Error reading video metadata: %s" % e, post_errors)
        return video_illust_url.width, video_illust_url.height
    video_stream = next(filter(lambda x: x['codec_type'] == 'video', probe['streams']), None)
    if video_stream is None:
        create_post_error('logical.downloader.base.check_video_dimensions', "No video streams found: %e" % video_illust_url.url, post_errors)
        return video_illust_url.width, video_illust_url.height
    if (video_illust_url.width and video_stream['width'] != video_illust_url.width) or (video_illust_url.height and video_stream['height'] != video_illust_url.height):
        create_post_error('logical.downloader.base.check_video_dimensions', "Mismatching image dimensions: Reported - %d x %d, Actual - %d x %d" % (video_illust_url.width, video_illust_url.height, video_stream['width'], video_stream['height']), post_errors)
    return video_stream['width'], video_stream['height']


# #### Create media functions

def create_preview(image, post, downsample=True):
    try:
        preview = image.copy().convert("RGB")
        if downsample:
            preview.thumbnail(PREVIEW_DIMENSIONS)
        create_directory(post.preview_path)
        print("Saving preview:", post.preview_path)
        preview.save(post.preview_path, "JPEG")
    except Exception as e:
        return create_error('logical.downloader.base.create_preview', "Error creating preview: %s" % repr(e))


def create_sample(image, post, downsample=True):
    try:
        sample = image.copy().convert("RGB")
        if downsample:
            sample.thumbnail(SAMPLE_DIMENSIONS)
        create_directory(post.sample_path)
        print("Saving sample:", post.sample_path)
        sample.save(post.sample_path, "JPEG")
    except Exception as e:
        return create_error('logical.downloader.base.create_sample', "Error creating sample: %s" % repr(e))


def create_data(buffer, post):
    create_directory(post.file_path)
    print("Saving data:", post.file_path)
    put_get_raw(post.file_path, 'wb', buffer)


# #### Save functions

# ###### Image illust

def save_image(buffer, image, post, post_errors):
    try:
        create_data(buffer, post)
    except Exception as e:
        create_post_error('logical.downloader.base.save_image', "Error saving image to disk: %s" % repr(e), post_errors)
        return False
    if post.has_preview:
        error = create_preview(image, post)
        if error is not None:
            post_errors.append(error)
    if post.has_sample:
        error = create_sample(image, post)
        if error is not None:
            post_errors.append(error)
    return True


# ###### Video illust

def save_video(buffer, post):
    try:
        create_data(buffer, post)
    except Exception as e:
        return create_error('logical.downloader.base.save_video', "Error saving video to disk: %s" % repr(e))


def save_thumb(buffer, post, post_errors):
    image = load_image(buffer)
    if is_error(image):
        post_errors.append(image)
        return
    post.width = image.width
    post.height = image.height
    downsample = post.has_preview
    error = create_preview(image, post, downsample)
    if error is not None:
        post_errors.append(error)
    downsample = post.has_sample
    error = create_sample(image, post, downsample)
    if error is not None:
        post_errors.append(error)
