# APP/LOGICAL/RECORDS/MEDIA_FILE_REC.PY

# ## PYTHON IMPORTS
from concurrent.futures import ThreadPoolExecutor

# ## PACKAGE IMPORTS
from utility.data import get_buffer_checksum
from utility.file import create_directory, put_get_raw, delete_file

# ## LOCAL IMPORTS
from ... import SESSION
from ..network import get_http_data
from ..database.media_file_db import create_media_file_from_parameters, batch_delete_media_files,\
    get_media_file_by_url, get_media_files_by_md5s, update_media_file_expires, get_media_file_by_id,\
    is_media_file


# ## FUNCTIONS

def batch_delete_media(media_files):
    md5_list = [media.md5 for media in media_files]
    matching_records = get_media_files_by_md5s(md5_list)
    for media in media_files:
        # Multiple media file records can map to the same MD5 hash so only delete if the records
        # being deleted matches the total count
        delete_count = sum(1 for _ in filter(lambda x: x.md5 == media.md5, media_files))
        usage_count = sum(1 for _ in filter(lambda x: x.md5 == media.md5, matching_records))
        if delete_count == usage_count:
            delete_file(media.file_path)
    batch_delete_media_files(media_files)


def batch_get_or_create_media(media_batches):
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(get_or_create_media, url, source) for (url, source) in media_batches]
        results = [f.result() for f in futures]
        return [(get_media_file_by_id(item) if isinstance(item, int) else item) for item in results]


def get_or_create_media(download_url, source):
    media_file = get_media_file_by_url(download_url)
    if media_file is None:
        media_file = create_media(download_url, source)
    else:
        update_media_file_expires(media_file)
    results = media_file.id if is_media_file(media_file) else media_file
    SESSION.remove()
    return results


def create_media(download_url, source):
    buffer = get_http_data(download_url, headers=source.IMAGE_HEADERS)
    if type(buffer) is str:
        return buffer
    md5 = get_buffer_checksum(buffer)
    extension = source.get_media_extension(download_url)
    media_file = create_media_file_from_parameters({'md5': md5, 'file_ext': extension, 'media_url': download_url})
    try:
        create_directory(media_file.media.original_file_path)
        put_get_raw(media_file.media.original_file_path, 'wb', buffer)
    except Exception as e:
        delete_file(media_file.media.original_file_path)
        batch_delete_media_files([media_file])
        return "Exception creating media file on disk: %s" % str(e)
    return media_file
