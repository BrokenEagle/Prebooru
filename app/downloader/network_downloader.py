# APP/DOWNLOADER/NETWORK_DOWNLOADER.PY

# ##PYTHON IMPORTS
import requests

# ##LOCAL IMPORTS
from ..logical.network import GetHTTPFile
from ..database.post_db import CreatePostAndAddIllustUrl
from ..database.error_db import CreateError, CreateAndAppendError, ExtendErrors, IsError
from .base_downloader import ConvertImageUpload, ConvertVideoUpload, LoadImage, CheckExisting, CheckFiletype,\
    CheckImageDimensions, CheckVideoDimensions, SaveImage, SaveVideo, SaveThumb


# ##FUNCTIONS

# #### Main execution functions

def ConvertNetworkUpload(illust, upload, source):
    if source.IllustHasVideos(illust):
        return ConvertVideoUpload(illust, upload, source, CreateVideoPost)
    elif source.IllustHasImages(illust):
        all_upload_urls = [source.NormalizeImageURL(upload_url.url) for upload_url in upload.image_urls]
        image_illust_urls = [illust_url for illust_url in source.ImageIllustDownloadUrls(illust)
                             if (len(all_upload_urls) == 0) or (illust_url.url in all_upload_urls)]
        return ConvertImageUpload(image_illust_urls, upload, source, CreateImagePost)
    CreateAndAppendError('downloader.file_uploader.ConvertFileUpload', "No valid illust URLs.", upload)
    return False


# #### Network functions

def DownloadMedia(illust_url, source):
    download_url = source.GetFullUrl(illust_url)
    file_ext = source.GetMediaExtension(download_url)
    if file_ext not in ['jpg', 'png', 'mp4']:
        return CreateError('downloader.network_downloader.DownloadMedia', "Unsupported file format: %s" % file_ext), None
    print("Downloading", download_url)
    buffer = GetHTTPFile(download_url, headers=source.IMAGE_HEADERS)
    if isinstance(buffer, Exception):
        return CreateError('downloader.network_downloader.DownloadMedia', str(buffer)), None
    if isinstance(buffer, requests.Response):
        return CreateError('downloader.network_downloader.DownloadMedia', "HTTP %d - %s" % (buffer.status_code, buffer.reason)), None
    return buffer, file_ext


# #### Post creation functions

def CreateImagePost(image_illust_url, upload, source):
    buffer, file_ext = DownloadMedia(image_illust_url, source)
    if IsError(buffer):
        return [buffer]
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
    buffer, file_ext = DownloadMedia(video_illust_url, source)
    if IsError(buffer):
        return [buffer]
    md5 = CheckExisting(buffer, video_illust_url)
    if IsError(md5):
        return [md5]
    post_errors = []
    video_file_ext = CheckFiletype(buffer, file_ext, post_errors)
    filepath = SaveVideo(buffer, md5, video_file_ext)
    if IsError(filepath):
        return post_errors + [filepath]
    video_width, video_height = CheckVideoDimensions(filepath, video_illust_url, post_errors)
    thumb_binary, _ = DownloadMedia(thumb_illust_url, source)
    if IsError(thumb_binary):
        return post_errors + [thumb_binary]
    SaveThumb(thumb_binary, md5, source, post_errors)
    post = CreatePostAndAddIllustUrl(video_illust_url, video_width, video_height, video_file_ext, md5, len(buffer))
    if len(post_errors):
        ExtendErrors(post, post_errors)
    return post
