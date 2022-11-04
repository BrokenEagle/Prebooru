# APP/LOGICAL/RECORDS/POST_REC.PY

# ### PYTHON IMPORTS
import os
import threading

# ### PACKAGE IMPORTS
from config import TEMP_DIRECTORY, ALTERNATE_MOVE_DAYS
from utility.data import get_buffer_checksum
from utility.file import create_directory, put_get_raw, copy_file, delete_file
from utility.uprint import print_error, exception_print

# ### LOCAL IMPORTS
from ... import SESSION
from ..utility import set_error
from ..network import get_http_data
from ..media import load_image, create_sample, create_preview, create_video_screenshot, convert_mp4_to_webp,\
    convert_mp4_to_webm
from ..database.post_db import create_post_from_raw_parameters, delete_post, post_append_illust_url, get_post_by_md5,\
    get_posts_to_query_danbooru_id_page, update_post_from_parameters, set_post_alternate, alternate_posts_query,\
    get_all_posts_page
from ..database.illust_url_db import get_illust_url_by_url
from ..database.notation_db import create_notation_from_raw_parameters
from ..database.error_db import create_error_from_raw_parameters, create_error
from ..database.archive_db import get_archive, create_archive, update_archive, set_archive_temporary,\
    process_archive_data


# ## GLOBAL VARIABLES

RELOCATE_PAGE_LIMIT = 10


# ## FUNCTIONS

def check_all_posts_for_danbooru_id():
    print("Checking all posts for Danbooru ID.")
    page = get_posts_to_query_danbooru_id_page(5000)
    while True:
        print(f"check_all_posts_for_danbooru_id: {page.first} - {page.last} / Total({page.count})")
        if len(page.items) == 0 or not check_posts_for_danbooru_id(page.items):
            return
        if not page.has_next:
            return
        page = page.next()


def check_posts_for_danbooru_id(posts):
    from ..sources.danbooru import get_danbooru_posts_by_md5s
    post_md5s = [post.md5 for post in posts]
    for i in range(0, len(post_md5s), 1000):
        md5_sublist = post_md5s[i: i + 1000]
        results = get_danbooru_posts_by_md5s(md5_sublist)
        if results['error']:
            print(results['message'])
            return False
        if len(results['posts']) > 0:
            for post in posts:
                danbooru_post = next(filter(lambda x: x['md5'] == post.md5, results['posts']), None)
                if danbooru_post is None:
                    continue
                update_post_from_parameters(post, {'danbooru_id': danbooru_post['id']})
    return True


def check_posts_for_valid_md5():
    from ..downloader.network import redownload_post
    page = get_all_posts_page(100)
    while True:
        print(f"check_posts_for_valid_md5: {page.first} - {page.last} / Total({page.count})")
        for post in page.items:
            buffer = put_get_raw(post.file_path, 'rb')
            checksum = get_buffer_checksum(buffer)
            if post.md5 != checksum:
                print("\nMISMATCHING CHECKSUM: post #", post.id)
                for illust_url in post.illust_urls:
                    if redownload_post(post, illust_url):
                        break
                else:
                    print("Unable to download!", 'post #', post.id)
            print(".", end="", flush=True)
        if not page.has_next:
            break
        page = page.next()


def move_post_media_to_alternate(post, reverse=False):
    temppost = post.copy()
    temppost.alternate = not reverse
    copy_file(post.file_path, temppost.file_path, True)
    if post.has_sample:
        copy_file(post.sample_path, temppost.sample_path)
    if post.has_preview:
        copy_file(post.preview_path, temppost.preview_path)
    if post.is_video:
        copy_file(post.video_sample_path, temppost.video_sample_path)
        copy_file(post.video_preview_path, temppost.video_preview_path)
    # Commit post as alternate location at this point since the files have been safely copied over
    set_post_alternate(post, not reverse)
    # Any errors after this point will just leave orphan images, which can always be cleaned up later
    temppost.alternate = reverse
    delete_file(temppost.file_path)
    if post.has_sample:
        delete_file(temppost.sample_path)
    if post.has_preview:
        delete_file(temppost.preview_path)
    if post.is_video:
        delete_file(temppost.video_sample_path)
        delete_file(temppost.video_preview_path)


def delete_post_and_media(post):
    """Hard delete. Continue as long as post record gets deleted."""
    retdata = {'error': False, 'is_deleted': False}
    temppost = post.copy()
    retdata = _delete_post_data(post, retdata)
    if retdata['error']:
        print("delete_post_and_media-error:", retdata)
        return retdata
    retdata = _delete_media_files(temppost, retdata)
    if not retdata['error']:
        retdata['is_deleted'] = True
    return retdata


def archive_post_for_deletion(post, expires):
    """Soft delete. Preserve data at all costs."""
    retdata = {'error': False, 'is_deleted': False}
    temppost = post.copy()
    retdata, archive = _archive_post_data(post, retdata, expires)
    if retdata['error']:
        return retdata
    retdata = _copy_media_files(post, archive, retdata, True, False)
    if retdata['error']:
        return retdata
    retdata['is_deleted'] = True
    retdata = _delete_post_data(post, retdata)
    if retdata['error']:
        return retdata
    return _delete_media_files(temppost, retdata)


def reinstantiate_archived_post(archive, create_sample):
    retdata = {'error': False}
    post = get_post_by_md5(archive.data['body']['md5'])
    if post is not None:
        return set_error(retdata, "Post with MD5 %s already exists: post #%d" % (post.md5, post.id))
    try:
        post = create_post_from_raw_parameters(process_archive_data(archive.data['body']))
    except Exception as e:
        return set_error(retdata, "Error creating post: %s" % str(e))
    retdata = _copy_media_files(post, archive, retdata, False, True)
    if retdata['error']:
        delete_post(post)
        return retdata
    retdata['item'] = post.to_json()
    # Once the file move is successful, keep going even if there are errors.
    create_sample_preview_files(post, retdata)
    if post.is_video:
        threading.Thread(target=create_video_sample_preview_files,
                         args=(post.file_path, post.video_preview_path,
                               post.video_sample_path, create_sample)).start()
    relink_archived_post(archive, post)
    for notation_data in archive.data['relations']['notations']:
        notation = create_notation_from_raw_parameters(notation_data)
        post.notations.append(notation)
        SESSION.commit()
    for error_data in archive.data['relations']['errors']:
        error = create_error_from_raw_parameters(error_data)
        post.errors.append(error)
        SESSION.commit()
    set_archive_temporary(archive, 7)
    return retdata


def create_sample_preview_files(post, retdata=None):
    retdata = retdata or {'error': False}
    errors = []
    buffer = None
    if post.is_video:
        buffer = _get_video_thumb_binary(post)
    if buffer is not None:
        has_sample = has_preview = True
        downsample_sample = post.has_sample
        downsample_preview = post.has_preview
    else:
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


def create_video_sample_preview_files(file_path, vpreview_path, vsample_path, create_sample):
    convert_mp4_to_webp(file_path, vpreview_path)
    if create_sample:
        convert_mp4_to_webm(file_path, vsample_path)


def relink_archived_post(archive, post=None):
    if post is None:
        post = get_post_by_md5(archive.data['body']['md5'])
        if post is None:
            return "No post found with MD5 %s" % archive.data['body']['md5']
    for link_data in archive.data['links']['illusts']:
        illust_url = get_illust_url_by_url(site=link_data['site'], partial_url=link_data['url'])
        if illust_url is not None:
            post_append_illust_url(post, illust_url)


def relocate_old_posts_to_alternate(manual):
    if ALTERNATE_MOVE_DAYS is None:
        return
    moved = 0
    max_pages = RELOCATE_PAGE_LIMIT if not manual else float('inf')
    query = alternate_posts_query(ALTERNATE_MOVE_DAYS)
    page = query.limit_paginate(per_page=50)
    while True:
        print(f"relocate_old_posts_to_alternate: {page.first} - {page.last} / Total({page.count})")
        for post in page.items:
            print(f"Moving {post.shortlink}")
            move_post_media_to_alternate(post)
            moved += 1
        if not page.has_next or page.page > max_pages:
            return moved
        page = page.next()


# #### Private functions

def _archive_post_data(post, retdata, expires):
    data = {
        'body': post.archive_dict(),
        'scalars': {},
        'relations': {
            'notations': [notation.archive_dict() for notation in post.notations],
            'errors': [error.archive_dict() for error in post.errors],
        },
        'links': {
            'illusts': [{'url': illust_url.url, 'site': illust_url.site}
                        for illust_url in post.illust_urls],
        },
    }
    archive = get_archive('post', post.md5)
    try:
        if archive is None:
            archive = create_archive('post', post.md5, data, expires)
        else:
            update_archive(archive, data, expires)
    except Exception as e:
        print_error("Error archiving data: %s" % str(e))
        exception_print(e)
        return set_error(retdata, "Error archiving data: %s" % repr(e)), None
    return retdata, archive


def _delete_post_data(post, retdata):
    try:
        delete_post(post)
    except Exception as e:
        SESSION.rollback()
        return set_error(retdata, "Error deleting post: %s" % str(e))
    return retdata


def _copy_media_files(post, archive, retdata, copy_preview, reverse):
    from_item, to_item = (post, archive) if not reverse else (archive, post)
    print(f"Copying file: {from_item.file_path} -> {to_item.file_path}")
    create_directory(to_item.file_path)
    try:
        copy_file(from_item.file_path, to_item.file_path, True)
    except Exception as e:
        return set_error(retdata, "Error moving post file: %s" % str(e))
    if copy_preview and post.has_preview:
        print(f"Copying preview: {from_item.preview_path} -> {to_item.preview_path}")
        try:
            copy_file(from_item.preview_path, to_item.preview_path)
        except Exception:
            pass
    return retdata


def _delete_media_files(post, retdata):
    media_paths = {
        'file': post.file_path,
        'sample': post.sample_path,
        'preview': post.preview_path,
        'video_sample': post.video_sample_path,
        'video_preview': post.video_preview_path,
    }
    error_messages = []
    for key in media_paths:
        if media_paths[key] is not None:
            print(f"Deleting {key} file: {media_paths[key]}")
            try:
                delete_file(media_paths[key])
            except Exception as e:
                error_messages.append(f"Error deleting {key} file: {str(e)}")
    if len(error_messages) > 0:
        return set_error(retdata, '\r\n'.join(error_messages))
    return retdata


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
        create_directory(TEMP_DIRECTORY)
        save_path = os.path.join(TEMP_DIRECTORY, post.md5 + '.' + 'jpg')
        create_video_screenshot(post.file_path, save_path)
        buffer = put_get_raw(save_path, 'rb')
        delete_file(save_path)
        has_sample = has_preview = True
        downsample_sample = post.has_sample
        downsample_preview = post.has_preview
    return buffer, has_sample, has_preview, downsample_sample, downsample_preview


def _get_video_thumb_binary(post):
    for illust_url in post.illust_urls:
        source = illust_url.site.source
        download_url = source.get_sample_url(illust_url)
        print("Downloading", download_url)
        buffer = get_http_data(download_url, headers=source.IMAGE_HEADERS)
        if isinstance(buffer, str):
            create_error('records.post_rec._get_video_thumb_binary', "Download URL: %s => %s" % (download_url, buffer))
            continue
        return buffer
