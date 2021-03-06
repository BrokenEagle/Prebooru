# APP/LOGICAL/DOWNLOADER/BASE.PY

# ## PYTHON IMPORTS
import ffmpeg
import filetype
from PIL import Image
from io import BytesIO

# ## PACKAGE IMPORTS
from config import PREVIEW_DIMENSIONS, SAMPLE_DIMENSIONS
from utility.data import get_buffer_checksum
from utility.file import create_directory, put_get_raw

# ## LOCAL IMPORTS
from ..database.upload_db import add_upload_success, add_upload_failure, upload_append_post
from ..database.subscription_pool_element_db import add_subscription_post, update_subscription_pool_element_active,\
    check_deleted_subscription_post, update_subscription_pool_element_status, duplicate_subscription_post
from ..database.post_db import post_append_illust_url, get_post_by_md5
from ..database.error_db import create_error, create_and_append_error, extend_errors, is_error


# ## FUNCTIONS

# #### Main execution functions

def convert_video_upload(illust_url, upload, source, create_video_func, post_type):
    if illust_url.sample is None:
        msg = "Did not find thumbnail for video on illust #%d" % illust_url.illust_id
        create_and_append_error('logical.downloader.convert_video_upload', msg, upload)
        return False
    else:
        post = create_video_func(illust_url, upload, source, post_type)
        return record_outcome(post, upload)


def convert_image_upload(illust_urls, upload, source, create_image_func, post_type):
    result = False
    for illust_url in illust_urls:
        post = create_image_func(illust_url, upload, source, post_type)
        result = record_outcome(post, upload) or result
    return result


# #### Helper functions

def record_outcome(post, record):
    if isinstance(post, list):
        post_errors = post
        valid_errors = [error for error in post_errors if is_error(error)]
        if len(valid_errors) != len(post_errors):
            print("\aInvalid data returned in outcome:", [item for item in post_errors if not is_error(item)])
        extend_errors(record, valid_errors)
        if record.model_name == 'upload':
            add_upload_failure(record)
        elif record.model_name == 'subscription_pool_element' and record.status == 'active':
            update_subscription_pool_element_active(record, False)
            update_subscription_pool_element_status(record, 'error')
        return False
    if record.model_name == 'upload':
        upload_append_post(record, post)
        add_upload_success(record)
    elif record.model_name == 'subscription_pool_element':
        add_subscription_post(record, post)
    return True


def load_image(buffer):
    try:
        file_imgdata = BytesIO(buffer)
        image = Image.open(file_imgdata)
    except Exception as e:
        return create_error('downloader.base.load_image', "Error processing image data: %s" % repr(e))
    return image


def create_post_error(function, message, post_errors, module='downloader.base'):
    error = create_error(f'{module}.{function}', message)
    post_errors.append(error)


# #### Validation functions

def check_existing(buffer, illust_url, record):
    md5 = get_buffer_checksum(buffer)
    post = get_post_by_md5(md5)
    if post is not None:
        post_append_illust_url(post, illust_url)
        if record.model_name == 'subscription_pool_element':
            duplicate_subscription_post(record, post.md5)
        return create_error('downloader.base.check_existing', "Media already uploaded on post #%d" % post.id)
    if record.model_name == 'subscription_pool_element' and check_deleted_subscription_post(md5):
        duplicate_subscription_post(record, md5)
        return create_error('downloader.base.check_existing', "Media already marked as deleted: %s" % md5)
    return md5


def check_filetype(buffer, file_ext, post_errors):
    try:
        guess = filetype.guess(buffer)
    except Exception as e:
        msg = "Error reading file headers: %s" % repr(e)
        create_post_error('check_filetype', msg, post_errors)
        return file_ext
    if guess and guess.extension != file_ext:
        msg = "Mismatching file extensions: Reported - %s, Actual - %s" % (file_ext, guess.extension)
        create_post_error('check_filetype', msg, post_errors)
        file_ext = guess.extension
    return file_ext


def check_image_dimensions(image, illust_url, post_errors):
    if (illust_url.width and image.width != illust_url.width) or\
       (illust_url.height and image.height != illust_url.height):
        msg = "Mismatching image dimensions: Reported - %d x %d, Actual - %d x %d" %\
              (illust_url.width, illust_url.height, image.width, image.height)
        create_post_error('save_image', msg, post_errors)
    return image.width, image.height


def check_video_dimensions(post, illust_url, post_errors):
    try:
        probe = ffmpeg.probe(post.file_path)
    except FileNotFoundError:
        msg = "Must install ffprobe.exe. See Github page for details."
        create_post_error('check_video_dimensions', msg, post_errors)
        return illust_url.width, illust_url.height
    except Exception as e:
        msg = "Error reading video metadata: %s" % repr(e)
        create_post_error('check_video_dimensions', msg, post_errors)
        return illust_url.width, illust_url.height
    video_stream = next(filter(lambda x: x['codec_type'] == 'video', probe['streams']), None)
    if video_stream is None:
        msg = "No video streams found: %e" % illust_url.url
        create_post_error('check_video_dimensions', msg, post_errors)
        return illust_url.width, illust_url.height
    if (illust_url.width and video_stream['width'] != illust_url.width) or\
       (illust_url.height and video_stream['height'] != illust_url.height):
        msg = "Mismatching image dimensions: Reported - %d x %d, Actual - %d x %d" %\
              (illust_url.width, illust_url.height, video_stream['width'], video_stream['height'])
        create_post_error('check_video_dimensions', msg, post_errors)
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
        return create_error('downloader.base.create_preview', "Error creating preview: %s" % repr(e))


def create_sample(image, post, downsample=True):
    try:
        sample = image.copy().convert("RGB")
        if downsample:
            sample.thumbnail(SAMPLE_DIMENSIONS)
        create_directory(post.sample_path)
        print("Saving sample:", post.sample_path)
        sample.save(post.sample_path, "JPEG")
    except Exception as e:
        return create_error('downloader.base.create_sample', "Error creating sample: %s" % repr(e))


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
        msg = "Error saving image to disk: %s" % repr(e)
        create_post_error('save_image', msg, post_errors)
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
        return create_error('downloader.base.save_video', "Error saving video to disk: %s" % repr(e))


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
