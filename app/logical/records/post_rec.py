# APP/LOGICAL/RECORDS/POST_REC.PY

# ### PYTHON IMPORTS
import os

# ### EXTERNAL IMPORTS
from sqlalchemy.orm import selectinload

# ### PACKAGE IMPORTS
from config import TEMP_DIRECTORY, ALTERNATE_MOVE_DAYS
from utility.data import get_buffer_checksum, merge_dicts, inc_dict_entry
from utility.file import create_directory, put_get_raw, copy_file, delete_file
from utility.uprint import buffered_print

# ### LOCAL IMPORTS
from ... import SESSION
from ...models import Post, Artist
from ..utility import set_error, SessionThread
from ..logger import handle_error_message
from ..network import get_http_data
from ..media import load_image, create_sample, create_preview, create_video_screenshot, convert_mp4_to_webp,\
    convert_mp4_to_webm
from ..database.base_db import delete_record, commit_session
from ..database.post_db import\
    get_posts_to_query_danbooru_id_page, update_post_from_parameters, alternate_posts_query,\
    get_all_posts_page, missing_image_hashes_query, missing_similarity_matches_query, get_posts_by_id,\
    get_artist_posts_without_danbooru_ids
from ..database.error_db import create_and_append_error
from ..database.archive_db import set_archive_temporary
from .base_rec import delete_data
from .image_hash_rec import generate_post_image_hashes
from .similarity_match_rec import generate_similarity_matches
from .pool_rec import delete_pool_element
from .archive_rec import archive_record, recreate_record, recreate_scalars, recreate_attachments, recreate_links


# ## GLOBAL VARIABLES

RELOCATE_PAGE_LIMIT = 10


# ## FUNCTIONS

def check_all_posts_for_danbooru_id():
    print("Checking all posts for Danbooru ID.")
    status = {'total': 0}
    page = get_posts_to_query_danbooru_id_page(5000)
    while True:
        print(f"check_all_posts_for_danbooru_id: {page.first} - {page.last} / Total({page.count})")
        if len(page.items) == 0 or not check_posts_for_danbooru_id(page.items, status) or not page.has_next:
            return status
        page = page.next()


def check_artist_posts_for_danbooru_id(artist_id):
    artist = Artist.find(artist_id)
    page = get_artist_posts_without_danbooru_ids(artist)
    while True:
        print(f"check_artist_posts_for_danbooru_id: {page.first} - {page.last} / Total({page.count})")
        if len(page.items) == 0 or not check_posts_for_danbooru_id(page.items, {}) or not page.has_next:
            break
        page = page.next()


def check_posts_for_danbooru_id(posts, status=None):
    status = status or {}
    from ..sources.danbooru_src import get_danbooru_posts_by_md5s
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
                inc_dict_entry(status, 'total')
    return True


def check_posts_for_valid_md5():
    from ..downloader.network_dl import redownload_post
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
    alternate = not reverse
    temppost.alternate = alternate
    copy_file(post.file_path, temppost.file_path, True)
    if post.has_sample:
        copy_file(post.sample_path, temppost.sample_path)
    if post.has_preview:
        copy_file(post.preview_path, temppost.preview_path)
    if post.is_video:
        copy_file(post.video_sample_path, temppost.video_sample_path)
        copy_file(post.video_preview_path, temppost.video_preview_path)
    # Commit post as alternate location at this point since the files have been safely copied over
    update_post_from_parameters(post, {'alternate': alternate})
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
    retdata.update(delete_data(post, delete_post))
    if retdata['error']:
        return retdata
    error = _delete_media_files(temppost)
    if error is not None:
        return handle_error_message(error, retdata)
    retdata['is_deleted'] = True
    return retdata


def archive_post_for_deletion(post, expires=30):
    """Soft delete. Preserve data at all costs."""
    retdata = {'is_deleted': False}
    temppost = post.copy()
    archive = archive_record(post, expires)
    if archive is None:
        msg = f"Error archiving data [{post.shortlink}]."
        return handle_error_message(msg, retdata)
    retdata['item'] = archive.to_json()
    error = _copy_media_files(post, archive, True, False)
    if error is not None:
        return handle_error_message(error, retdata)
    retdata['is_deleted'] = True
    retdata.update(delete_data(post, delete_post))
    if retdata['error']:
        return retdata
    error = _delete_media_files(temppost)
    if error is not None:
        return handle_error_message(error, retdata)
    retdata['error'] = False
    return retdata


def recreate_archived_post(archive):
    try:
        recreate_data = merge_dicts(archive.data, {'body': {'alternate': False, 'simcheck': False}})
        post = recreate_record(Post, archive.key, recreate_data)
        recreate_scalars(post, archive.data)
        recreate_attachments(post, archive.data)
        recreate_links(post, archive.data)
    except Exception as e:
        SESSION.rollback()
        return handle_error_message(str(e))
    else:
        SESSION.commit()
    error = _copy_media_files(post, archive, False, True)
    if error is not None:
        delete_post(post)
        return handle_error_message(error)
    # Once the file move is successful, keep going even if there are errors.
    retdata = create_sample_preview_files(post)
    if post.is_video:
        SessionThread(target=create_video_sample_preview_files,
                      args=(post.file_path, post.video_preview_path,
                            post.video_sample_path, create_sample)).start()
    SessionThread(target=process_image_matches, args=([post.id],)).start()
    retdata['item'] = post.to_json()
    set_archive_temporary(archive, 7)
    return retdata


def relink_archived_post(archive):
    post = Post.find_by_key(archive.key)
    if post is None:
        return f"No post found with key {archive.key}"
    recreate_links(post, archive.data)


def generate_missing_image_hashes(manual):
    max_pages = 10 if not manual else float('inf')
    query = missing_image_hashes_query()
    query = query.options(selectinload(Post.subscription_element))
    page = query.limit_paginate(per_page=20)
    while page.count > 0:
        print(f"\ngenerate_missing_image_hashes: {page.first} - {page.last} / Total({page.count})\n")
        for post in page.items:
            generate_post_image_hashes(post)
            if post.subscription_element is None:
                generate_similarity_matches(post)
        SESSION.commit()
        if not page.has_next or page.page > max_pages:
            break
        page = page.next()
    return {'total': page.count}


def calculate_similarity_matches(manual):
    max_pages = 10 if not manual else float('inf')
    query = missing_similarity_matches_query()
    query = query.options(selectinload(Post.image_hashes))
    page = query.limit_paginate(per_page=50)
    while page.count > 0:
        print(f"\ngenerate_missing_image_hashes: {page.first} - {page.last} / Total({page.count})\n")
        for post in page.items:
            generate_similarity_matches(post)
        SESSION.commit()
        if not page.has_next or page.page > max_pages:
            break
        page = page.next()
    return {'total': page.count}


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


def process_image_matches(post_ids):
    printer = buffered_print("Process Image Matches")
    posts = get_posts_by_id(post_ids)
    for post in posts:
        generate_post_image_hashes(post, printer=printer)
        generate_similarity_matches(post, printer=printer)
    SESSION.commit()
    printer.print()


def delete_post(post):
    msg = "[%s]: deleted\n" % post.shortlink
    for pool_element in post._pools:
        delete_pool_element(pool_element)
    delete_record(post)
    commit_session()
    print(msg)


# #### Private functions

def _copy_media_files(post, archive, copy_preview, reverse):
    from_item, to_item = (post, archive) if not reverse else (archive, post)
    print(f"Copying file: {from_item.file_path} -> {to_item.file_path}")
    create_directory(to_item.file_path)
    try:
        copy_file(from_item.file_path, to_item.file_path, True)
    except Exception as e:
        return f"Error moving post file: {repr(e)}"
    if copy_preview and post.has_preview:
        print(f"Copying preview: {from_item.preview_path} -> {to_item.preview_path}")
        try:
            copy_file(from_item.preview_path, to_item.preview_path)
        except Exception:
            pass


def _delete_media_files(post):
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
        return '\r\n'.join(error_messages)


def _load_file(post):
    if post.file_ext in ['jpg', 'png', 'gif']:
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
            create_and_append_error(post, 'post_rec.get_video_thumb_binary',
                                    "Download URL: %s => %s" % (download_url, buffer))
            continue
        return buffer
