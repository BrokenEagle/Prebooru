# APP/LOGICAL/RECORDS/ARCHIVE_DATA_REC.PY

# ### LOCAL IMPORTS
from ..utility import set_error
from ..file import put_get_raw
from ..media import load_image, create_sample, create_preview


# ## FUNCTIONS

def create_sample_preview_files(post, retdata=None):
    retdata = retdata or {'error': False}
    errors = []
    buffer, has_sample, has_preview, downsample_sample, downsample_preview = _load_file(post)
    if type(buffer) is str:
        return set_error(retdata, buffer)
    image = load_image(buffer)
    if type(image) is str:
        return set_error(retdata, image)
    if has_sample:
        error = create_sample(image, post.sample_path, downsample_sample)
        if error is not None:
            errors.append(error)
    if has_preview:
        error = create_preview(image, post.preview_path, downsample_preview)
        if error is not None:
            errors.append(error)
    if len(errors):
        set_error(retdata, '\r\n'.join(errors))
    return retdata


# #### Private functions

def _load_file(post):
    if post.file_ext in ['jpg', 'png']:
        try:
            buffer = put_get_raw(post.file_path, 'rb')
        except Exception as e:
            return "Error loading post file: %s" % str(e), None, None, None, None
        has_sample = post.has_sample
        has_preview = post.has_preview
        downsample_sample = downsample_preview = True
    elif post.file_ext == 'gif':
        pass
    elif post.file_ext == 'mp4':
        has_sample = has_preview = True
        downsample_sample = post.has_sample
        downsample_preview = post.has_preview
        pass
    return buffer, has_sample, has_preview, downsample_sample, downsample_preview
