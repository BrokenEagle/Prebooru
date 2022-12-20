# APP/LOGICAL/DOWNLOADER/BASE_DL.PY

# ## PYTHON IMPORTS
import filetype

# ## PACKAGE IMPORTS
from utility.data import get_buffer_checksum

# ## LOCAL IMPORTS
from ..media import create_preview, create_sample, create_data, check_alpha, convert_alpha, load_image, get_video_info
from ..database.upload_element_db import update_upload_element_from_parameters
from ..database.subscription_element_db import link_subscription_post, update_subscription_element_status,\
    duplicate_subscription_post
from ..database.post_db import post_append_illust_url, get_post_by_md5, set_post_type
from ..database.error_db import create_error, extend_errors, is_error


# ## FUNCTIONS

# #### Helper functions

def record_outcome(post, record):
    if isinstance(post, list):
        post_errors = post
        valid_errors = [error for error in post_errors if is_error(error)]
        if len(valid_errors) != len(post_errors):
            print("\aInvalid data returned in outcome:", [item for item in post_errors if not is_error(item)])
        extend_errors(record, valid_errors)
        if record.model_name == 'subscription_element' and record.status.name == 'active':
            update_subscription_element_status(record, 'error')
        elif record.model_name == 'upload_element' and post.type.name != 'user':
            update_upload_element_from_parameters(record, {'status': 'error'})
        return False
    if record.model_name == 'upload_element':
        update_upload_element_from_parameters(record, {'status': 'complete', 'md5': post.md5})
    elif record.model_name == 'subscription_element':
        link_subscription_post(record, post)
    return True


def load_post_image(buffer):
    image = load_image(buffer)
    if isinstance(image, str):
        return create_error('downloader.base_dl.load_post_image', image)
    try:
        if check_alpha(image):
            return convert_alpha(image)
        else:
            return image
    except Exception as e:
        return create_error('downloader.base_dl.load_post_image', "Error removing alpha transparency: %s" % repr(e))


def create_post_error(function, message, post_errors, module='downloader.base_dl'):
    error = create_error(f'{module}.{function}', message)
    post_errors.append(error)


# #### Validation functions

def check_existing(buffer, illust_url, record):
    md5 = get_buffer_checksum(buffer)
    if record.model_name == 'post':
        return md5
    post = get_post_by_md5(md5)
    if post is not None:
        post_append_illust_url(post, illust_url)
        if record.model_name == 'upload_element':
            update_upload_element_from_parameters(record, {'status': 'duplicate', 'md5': post.md5})
            if post.type.name != 'user':
                set_post_type(post, 'user')
        elif record.model_name == 'subscription_element':
            duplicate_subscription_post(record, post.md5)
        return None
    if record.model_name == 'subscription_element':
        record.md5 = md5  # Set the MD5 now so that the count function can be used
        if record.duplicate_element_count > 1:
            duplicate_subscription_post(record, md5)
            return None
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


def check_video_info(post, illust_url, post_errors):
    info = get_video_info(post.file_path)
    if isinstance(info, str):
        create_post_error('check_video_info', info, post_errors)
        return illust_url.width, illust_url.height
    if (illust_url.width and info['width'] != illust_url.width) or\
       (illust_url.height and info['height'] != illust_url.height):
        msg = "Mismatching image dimensions: Reported - %d x %d, Actual - %d x %d" %\
              (illust_url.width, illust_url.height, info['width'], info['height'])
        create_post_error('check_video_info', msg, post_errors)
    return info


# #### Create media functions

def create_post_preview(image, post, downsample=True):
    result = create_preview(image, post.preview_path, downsample)
    if result is not None:
        return create_error('downloader.base_dl.create_post_preview', result)


def create_post_sample(image, post, downsample=True):
    result = create_sample(image, post.sample_path, downsample)
    if result is not None:
        return create_error('downloader.base_dl.create_post_sample', result)


def create_post_data(buffer, post):
    result = create_data(buffer, post.file_path)
    if result is not None:
        return create_error('downloader.base_dl.create_post_data', result)


# #### Save functions

# ###### Image illust

def save_image(buffer, image, post, post_errors):
    error = create_post_data(buffer, post)
    if error is not None:
        post_errors.append(error)
        return False
    if post.has_preview:
        error = create_post_preview(image, post)
        if error is not None:
            post_errors.append(error)
    if post.has_sample:
        error = create_post_sample(image, post)
        if error is not None:
            post_errors.append(error)
    return True


# ###### Video illust

def save_video(buffer, post):
    return create_post_data(buffer, post)


def save_thumb(buffer, post, post_errors):
    image = load_post_image(buffer)
    if is_error(image):
        post_errors.append(image)
        return
    post.width = image.width
    post.height = image.height
    downsample = post.has_preview
    error = create_post_preview(image, post, downsample)
    if error is not None:
        post_errors.append(error)
    downsample = post.has_sample
    error = create_post_sample(image, post, downsample)
    if error is not None:
        post_errors.append(error)
