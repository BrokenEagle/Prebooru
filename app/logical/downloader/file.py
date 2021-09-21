# APP/LOGICAL/DOWNLOADER/FILE.PY

# ## LOCAL IMPORTS
from ..utility import GetFileExtension
from ..file import PutGetRaw
from ...models import Post
from ...database.post_db import CreatePostAndAddIllustUrl
from ...database.error_db import CreateAndAppendError, ExtendErrors, IsError
from .base import ConvertImageUpload, ConvertVideoUpload, LoadImage, CheckExisting, CheckFiletype,\
    CheckImageDimensions, CheckVideoDimensions, SaveImage, SaveVideo, SaveThumb


# ## FUNCTIONS

def ConvertFileUpload(upload, source):
    illust_url = upload.illust_url
    illust = illust_url.illust
    if source.IllustHasVideos(illust):
        if upload.sample_filepath is None:
            CreateAndAppendError('logical.downloader.file.ConvertFileUpload', "Must include sample filepath on video uploads (illust #%d)." % illust.id, upload)
        else:
            return ConvertVideoUpload(illust, upload, source, CreateVideoPost)
    elif source.IllustHasImages(illust):
        return ConvertImageUpload([illust_url], upload, source, CreateImagePost)
    CreateAndAppendError('logical.downloader.file.ConvertFileUpload', "No valid illust URLs.", upload)
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
    temppost = Post(md5=md5, file_ext=image_file_ext, width=image_width, height=image_height)
    if not SaveImage(buffer, image, temppost, post_errors):
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
    temppost = Post(md5=md5, file_ext=video_file_ext)
    error = SaveVideo(buffer, temppost)
    if error is not None:
        return post_errors + [error]
    video_width, video_height = CheckVideoDimensions(temppost, video_illust_url, post_errors)
    thumb_binary = PutGetRaw(upload.sample_filepath, 'rb')
    SaveThumb(thumb_binary, temppost, post_errors)
    post = CreatePostAndAddIllustUrl(video_illust_url, video_width, video_height, video_file_ext, md5, len(buffer))
    if len(post_errors):
        ExtendErrors(post, post_errors)
    return post
