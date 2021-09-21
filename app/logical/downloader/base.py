# APP/LOGICAL/DOWNLOADER/BASE.PY

# ## PYTHON IMPORTS
import ffmpeg
import filetype
from PIL import Image
from io import BytesIO

# ## LOCAL IMPORTS
from ..utility import GetBufferChecksum
from ..file import CreateDirectory, PutGetRaw
from ...config import PREVIEW_DIMENSIONS, SAMPLE_DIMENSIONS
from ...database.upload_db import AddUploadSuccess, AddUploadFailure, UploadAppendPost
from ...database.post_db import PostAppendIllustUrl, GetPostByMD5
from ...database.error_db import CreateError, CreateAndAppendError, ExtendErrors, IsError


# ## FUNCTIONS

# #### Main execution functions

def ConvertVideoUpload(illust, upload, source, create_video_func):
    video_illust_url, thumb_illust_url = source.VideoIllustDownloadUrls(illust)
    if thumb_illust_url is None:
        CreateAndAppendError('logical.downloader.ConvertVideoUpload', "Did not find thumbnail for video on illust #%d" % illust.id, upload)
        return False
    else:
        post = create_video_func(video_illust_url, thumb_illust_url, upload, source)
        return RecordOutcome(post, upload)


def ConvertImageUpload(illust_urls, upload, source, create_image_func):
    result = False
    for illust_url in illust_urls:
        post = create_image_func(illust_url, upload, source)
        result = RecordOutcome(post, upload) or result
    return result


# #### Helper functions

def RecordOutcome(post, upload):
    if isinstance(post, list):
        post_errors = post
        valid_errors = [error for error in post_errors if IsError(error)]
        if len(valid_errors) != len(post_errors):
            print("\aInvalid data returned in outcome:", [item for item in post_errors if not IsError(item)])
        ExtendErrors(upload, valid_errors)
        AddUploadFailure(upload)
        return False
    else:
        UploadAppendPost(upload, post)
        AddUploadSuccess(upload)
        return True


def LoadImage(buffer):
    try:
        file_imgdata = BytesIO(buffer)
        image = Image.open(file_imgdata)
    except Exception as e:
        return CreateError('logical.downloader.base.LoadImage', "Error processing image data: %s" % repr(e))
    return image


def CreatePostError(module, message, post_errors):
    error = CreateError(module, message)
    post_errors.append(error)


# #### Validation functions

def CheckExisting(buffer, illust_url):
    md5 = GetBufferChecksum(buffer)
    post = GetPostByMD5(md5)
    if post is not None:
        PostAppendIllustUrl(post, illust_url)
        return CreateError('logical.downloader.base.CheckExisting', "Image already uploaded on post #%d" % post.id)
    return md5


def CheckFiletype(buffer, file_ext, post_errors):
    try:
        guess = filetype.guess(buffer)
    except Exception as e:
        CreatePostError('logical.downloader.base.CheckFiletype', "Error reading file headers: %s" % repr(e), post_errors)
        return file_ext
    if guess.extension != file_ext:
        CreatePostError('logical.downloader.base.CheckFiletype', "Mismatching file extensions: Reported - %s, Actual - %s" % (file_ext, guess.extension), post_errors)
        file_ext = guess.extension
    return file_ext


def CheckImageDimensions(image, image_illust_url, post_errors):
    if (image_illust_url.width and image.width != image_illust_url.width) or (image_illust_url.height and image.height != image_illust_url.height):
        CreatePostError('logical.downloader.base.SaveImage', "Mismatching image dimensions: Reported - %d x %d, Actual - %d x %d" % (image_illust_url.width, image_illust_url.height, image.width, image.height), post_errors)
    return image.width, image.height


def CheckVideoDimensions(post, video_illust_url, post_errors):
    try:
        probe = ffmpeg.probe(post.file_path)
    except FileNotFoundError:
        CreatePostError('logical.downloader.base.CheckVideoDimensions', "Must install ffprobe.exe. See Github page for details.", post_errors)
        return video_illust_url.width, video_illust_url.height
    except Exception as e:
        CreatePostError('logical.downloader.base.CheckVideoDimensions', "Error reading video metadata: %s" % e, post_errors)
        return video_illust_url.width, video_illust_url.height
    video_stream = next(filter(lambda x: x['codec_type'] == 'video', probe['streams']), None)
    if video_stream is None:
        CreatePostError('logical.downloader.base.CheckVideoDimensions', "No video streams found: %e" % video_illust_url.url, post_errors)
        return video_illust_url.width, video_illust_url.height
    if (video_illust_url.width and video_stream['width'] != video_illust_url.width) or (video_illust_url.height and video_stream['height'] != video_illust_url.height):
        CreatePostError('logical.downloader.base.CheckVideoDimensions', "Mismatching image dimensions: Reported - %d x %d, Actual - %d x %d" % (video_illust_url.width, video_illust_url.height, video_stream['width'], video_stream['height']), post_errors)
    return video_stream['width'], video_stream['height']


# #### Create media functions

def CreatePreview(image, post, downsample=True):
    try:
        preview = image.copy().convert("RGB")
        if downsample:
            preview.thumbnail(PREVIEW_DIMENSIONS)
        CreateDirectory(post.preview_path)
        print("Saving preview:", post.preview_path)
        preview.save(post.preview_path, "JPEG")
    except Exception as e:
        return CreateError('logical.downloader.base.CreatePreview', "Error creating preview: %s" % repr(e))


def CreateSample(image, post, downsample=True):
    try:
        sample = image.copy().convert("RGB")
        if downsample:
            sample.thumbnail(SAMPLE_DIMENSIONS)
        CreateDirectory(post.sample_path)
        print("Saving sample:", post.sample_path)
        sample.save(post.sample_path, "JPEG")
    except Exception as e:
        return CreateError('logical.downloader.base.CreateSample', "Error creating sample: %s" % repr(e))


def CreateData(buffer, post):
    CreateDirectory(post.file_path)
    print("Saving data:", post.file_path)
    PutGetRaw(post.file_path, 'wb', buffer)


# #### Save functions

# ###### Image illust

def SaveImage(buffer, image, post, post_errors):
    try:
        CreateData(buffer, post)
    except Exception as e:
        CreatePostError('logical.downloader.base.SaveImage', "Error saving image to disk: %s" % repr(e), post_errors)
        return False
    if post.has_preview:
        error = CreatePreview(image, post)
        if error is not None:
            post_errors.append(error)
    if post.has_sample:
        error = CreateSample(image, post)
        if error is not None:
            post_errors.append(error)
    return True


# ###### Video illust

def SaveVideo(buffer, post):
    try:
        CreateData(buffer, post)
    except Exception as e:
        return CreateError('logical.downloader.base.SaveVideo', "Error saving video to disk: %s" % repr(e))


def SaveThumb(buffer, post, post_errors):
    image = LoadImage(buffer)
    if IsError(image):
        post_errors.append(image)
        return
    post.width = image.width
    post.height = image.height
    downsample = post.has_preview
    error = CreatePreview(image, post, downsample)
    if error is not None:
        post_errors.append(error)
    downsample = post.has_sample
    error = CreateSample(image, post, downsample)
    if error is not None:
        post_errors.append(error)
