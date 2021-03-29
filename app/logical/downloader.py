# APP/LOGICAL/DOWNLOADER.PY

# ##PYTHON IMPORTS
import requests

# ##LOCAL IMPORTS
from .utility import GetHTTPFilename, GetFileExtension, GetBufferChecksum
from .file import PutGetRaw
from .network import GetHTTPFile
from .. import database as DB
from ..config import workingdirectory, imagefilepath

# ##GLOBAL VARIABLES

IMAGE_DIRECTORY = workingdirectory + imagefilepath + 'prebooru\\'

ONE_DAY = 60 * 60 * 24

# ##FUNCTIONS


def DownloadMultipleImages(illust, upload, type, module):
    for i in range(0, len(illust['images'])):
        image_url = illust['images'][i]['url']
        post = DownloadImage(image_url, illust, upload, i, module)
        if post is None:
            continue
        if type == 'post':
            post['expires'] = ONE_DAY * 30
        elif type == 'subscription':
            post['expires'] = ONE_DAY * 7
    DB.local.SaveDatabase()


def DownloadSingleImage(illust, upload, module):
    # Download the image using the original path for old images that may still be on the server
    image_url = module.NormalizeImageURL(upload['request'])
    print("Image url:", image_url)
    DownloadImage(image_url, illust, upload, module)
    DB.local.SaveDatabase()


def DownloadImage(image_url, illust, upload, order, module):
    file = GetHTTPFilename(image_url)
    download_url = module.IMAGE_SERVER + image_url
    print("Downloading", download_url)
    buffer = GetHTTPFile(download_url, headers=module.IMAGE_HEADERS)
    if isinstance(buffer, Exception):
        upload['failures'] += 1
        upload['errors'].append(str(buffer))
        return
    if isinstance(buffer, requests.Response):
        upload['failures'] += 1
        upload['errors'].append("HTTP %d - %s" % (buffer.status_code, buffer.reason))
        return
    md5 = GetBufferChecksum(buffer)
    post = DB.local.FindBy('posts', 'md5', md5)
    if post is not None:
        upload['failures'] += 1
        upload['errors'].append("Image already uploaded on post #%d" % post['id'])
        return
    move_directory = '%s\\%s\\' % (md5[0:2], md5[2:4])
    save_file = md5 + '.' + GetFileExtension(file)
    print("Saving", IMAGE_DIRECTORY + move_directory + save_file)
    if PutGetRaw(IMAGE_DIRECTORY + move_directory + save_file, 'wb', buffer) < 0:
        upload['failures'] += 1
        upload['errors'].append("Error saving image to disk")
        return
    image_id = module.GetImageID(file)
    upload['successes'] += 1
    post = DB.local.CreatePost(illust['id'], image_id, illust['artist_id'], module.SITE_ID, move_directory + save_file, md5, len(buffer), order)
    upload['post_ids'].append(post['id'])
    return post
