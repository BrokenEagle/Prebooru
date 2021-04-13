# APP/LOGICAL/UPLOADER.PY

# ##LOCAL IMPORTS
from ..logical.utility import GetFileExtension
from ..logical.file import PutGetRaw
from ..database.post_db import CreatePostAndAddIllustUrl
from ..database.error_db import CreateAndAppendError, ExtendErrors, IsError
from .base_downloader import ConvertImageUpload, ConvertVideoUpload, LoadImage, CheckExisting, CheckFiletype,\
    CheckImageDimensions, CheckVideoDimensions, SaveImage, SaveVideo, SaveThumb

# ##FUNCTIONS


def ConvertFileUpload(upload, source):
    illust_url = upload.illust_url
    illust = illust_url.illust
    if source.IllustHasVideos(illust):
        if upload.sample_filepath is None:
            CreateAndAppendError('downloader.file_uploader.ConvertFileUpload', "Must include sample filepath on video uploads (illust #%d)." % illust.id, upload)
        else:
            return ConvertVideoUpload(illust, upload, source, CreateVideoPost)
    elif source.IllustHasImages(illust):
        return ConvertImageUpload([illust_url], upload, source, CreateImagePost)
    CreateAndAppendError('downloader.file_uploader.ConvertFileUpload', "No valid illust URLs.", upload)
    return False


# #### Post creation functions

def CreateImagePost(image_illust_url, upload, source):
    file_ext = GetFileExtension(upload.media_filepath)
    buffer = PutGetRaw(upload.media_filepath, 'rb')
    md5 = CheckExisting(buffer, image_illust_url)
    if IsError(md5):
        return [md5]
    post_errors = []
    image_file_ext = CheckFiletype(buffer, file_ext, post_errors)
    image = LoadImage(buffer)
    if IsError(image):
        return post_errors + [image]
    image_width, image_height = CheckImageDimensions(image, image_illust_url, post_errors)
    if not SaveImage(buffer, image, md5, image_file_ext, image_illust_url, post_errors):
        return post_errors
    post = CreatePostAndAddIllustUrl(image_illust_url, image_width, image_height, image_file_ext, md5, len(buffer))
    if len(post_errors):
        ExtendErrors(post, post_errors)
    return post


def CreateVideoPost(video_illust_url, thumb_illust_url, upload, source):
    file_ext = GetFileExtension(upload.media_filepath)
    buffer = PutGetRaw(upload.media_filepath, 'rb')
    md5 = CheckExisting(buffer, video_illust_url)
    if IsError(md5):
        return [md5]
    post_errors = []
    video_file_ext = CheckFiletype(buffer, file_ext, post_errors)
    filepath = SaveVideo(buffer, md5, video_file_ext)
    if IsError(filepath):
        return post_errors + [filepath]
    video_width, video_height = CheckVideoDimensions(filepath, video_illust_url, post_errors)
    thumb_binary = PutGetRaw(upload.sample_filepath, 'rb')
    SaveThumb(thumb_binary, md5, source, post_errors)
    post = CreatePostAndAddIllustUrl(video_illust_url, video_width, video_height, video_file_ext, md5, len(buffer))
    if len(post_errors):
        ExtendErrors(post, post_errors)
    return post
