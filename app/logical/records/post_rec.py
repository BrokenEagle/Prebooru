# APP/LOGICAL/RECORDS/POST_REC.PY

# ### PYTHON IMPORTS
import os
import uuid

# ### EXTERNAL IMPORTS
from sqlalchemy.orm import selectinload

# ### PACKAGE IMPORTS
from config import TEMP_DIRECTORY, ALTERNATE_MOVE_DAYS
from utility.data import get_buffer_checksum, merge_dicts, inc_dict_entry, encode_json
from utility.file import create_directory, put_get_raw, copy_file, delete_file, filename_join, put_get_json,\
    clear_directory, copy_directory
from utility.uprint import buffered_print, print_warning

# ### LOCAL IMPORTS
from ... import SESSION
from ...models import Post, Artist, ArchivePost, IllustUrl
from ..utility import set_error, SessionThread
from ..batch_loader import selectinload_batch_primary
from ..logger import handle_error_message
from ..network import get_http_data
from ..media import load_image, create_sample, create_preview, create_video_screenshot, convert_mp4_to_webp,\
    convert_mp4_to_webm, check_filetype, get_pixel_hash, check_alpha, convert_alpha, create_data, get_video_info
from ..database.base_db import delete_record, commit_session
from ..database.post_db import create_post_from_parameters,\
    get_posts_to_query_danbooru_id_query, update_post_from_parameters, alternate_posts_query,\
    missing_image_hashes_query, missing_similarity_matches_query, get_posts_by_id,\
    get_artist_posts_without_danbooru_ids_query, get_post_by_md5
from ..database.notation_db import create_notation_from_parameters
from ..database.error_db import create_error_from_parameters, create_and_append_error, create_and_extend_errors
from ..database.archive_db import create_archive_from_parameters, update_archive_from_parameters,\
    get_archive_by_post_md5
from ..database.archive_post_db import create_archive_post_from_parameters, update_archive_post_from_parameters
from ..database.subscription_element_db import update_subscription_element_from_parameters
from ..sources.danbooru_src import get_danbooru_posts_by_md5s
from .base_rec import delete_data, records_paginate
from .illust_rec import download_illust_url, download_illust_sample, download_illust_url_frames
from .image_hash_rec import generate_post_image_hashes
from .similarity_match_rec import generate_similarity_matches
from .pool_rec import delete_pool_element


# ## GLOBAL VARIABLES

RELOCATE_PAGE_LIMIT = 10


# ## FUNCTIONS

def create_image_post(record, post_type, get_buffer, duplicate_check):
    retdata = _single_file_check(record, get_buffer, duplicate_check)
    if retdata['md5'] is None or retdata['duplicate']:
        return retdata
    buffer = retdata['buffer']
    file_ext = check_filetype(buffer)
    if isinstance(file_ext, tuple):
        retdata['errors'].append(_module_error('create_image_post', file_ext[0]))
        file_ext = None
    if file_ext is None:
        file_ext = record.illust_url.url_extension
    image = _load_image(buffer)
    if isinstance(image, tuple):
        retdata['errors'].append(image)
        return retdata
    md5 = get_buffer_checksum(buffer)
    params = {
        'md5': md5,
        'size': len(buffer),
        'width': image.width,
        'height': image.height,
        'pixel_md5': get_pixel_hash(image),
        'file_ext': file_ext,
        'type_name': post_type,
    }
    temppost = Post(md5=md5, file_ext=file_ext)
    result = create_data(buffer, temppost.file_path)
    if result is not None:
        retdata['errors'].append(_module_error('create_image_post', result))
        return retdata
    # From this point forward, the post will be created and all errors attached to that post
    retdata['post'] = post = create_post_from_parameters(params)
    create_image_post_sample_preview_images(post, image)
    return retdata


def update_image_post(post, buffer, illust_url):
    file_ext = check_filetype(buffer)
    if isinstance(file_ext, tuple):
        create_and_append_error(post, *_module_error('create_image_post', file_ext[0]))
        file_ext = None
    if file_ext is None:
        file_ext = illust_url.url_extension
    image = _load_image(buffer)
    if isinstance(image, tuple):
        create_and_append_error(post, *image)
        return False
    md5 = get_buffer_checksum(buffer)
    params = {
        'md5': md5,
        'size': len(buffer),
        'width': image.width,
        'height': image.height,
        'pixel_md5': get_pixel_hash(image),
        'file_ext': file_ext,
    }
    temppost = Post(md5=md5, file_ext=file_ext)
    result = create_data(buffer, temppost.file_path)
    if result is not None:
        create_and_append_error(post, *_module_error('create_image_post', result))
        return False
    update_post_from_parameters(post, params)
    create_image_post_sample_preview_images(post, image)
    return True


def create_image_post_sample_preview_images(post, image):
    errors = []
    if post.has_sample:
        result = create_sample(image, post.sample_path, downsample=True)
        if result is not None:
            errors.append(_module_error('create_image_post', result))
    if post.has_preview:
        result = create_preview(image, post.preview_path, downsample=True)
        if result is not None:
            errors.append(_module_error('create_image_post', result))
    create_and_extend_errors(post, errors)


def create_ugoira_post(illust_url, post_type, duplicate_check):
    working_directory = os.path.join(TEMP_DIRECTORY, str(uuid.uuid4()))
    create_directory(working_directory)
    retdata = create_ugoira_post_0(illust_url, post_type, working_directory, duplicate_check)
    if retdata['cleanup']:
        print("Cleaning up working directory:", working_directory)
        clear_directory(working_directory)
    return retdata


def create_ugoira_post_0(illust_url, post_type, working_directory, duplicate_check):
    retdata = {'errors': [], 'md5': None, 'post': None, 'duplicate': False, 'cleanup': True}
    illust_data = illust_url.source.get_illust_api_data(illust_url.illust.site_illust_id)
    ugoira_data = illust_url.source.get_ugoira_data(illust_url.illust.site_illust_id)
    save_data = {
        'illustId': illust_data['illustId'],
        'userId': illust_data['userId'],
        'createDate': illust_data['createDate'],
        'uploadDate': illust_data['uploadDate'],
        'width': illust_data['width'],
        'height': illust_data['height'],
        'mime_type': ugoira_data['ugoira']['mime_type'],
        'frames': [],
    }
    combined_pixel_hash = get_buffer_checksum(encode_json(illust_url.frames).encode('utf'))
    combined_size = 0
    params = None
    for i, buffer in enumerate(download_illust_url_frames(illust_url)):
        if isinstance(buffer, tuple):
            retdata['errors'].append(buffer)
            return retdata
        if params is None:
            file_ext = check_filetype(buffer)
            if isinstance(file_ext, tuple):
                retdata['errors'].append(_module_error('create_ugoira_post', file_ext[0]))
                file_ext = None
            if file_ext is None:
                file_ext = illust_url.url_extension
            image = _load_image(buffer)
            if isinstance(image, tuple):
                retdata['errors'].append(image)
                return retdata
            params = {
                'width': image.width,
                'height': image.height,
                'file_ext': file_ext,
                'type_name': post_type,
                'ugoira_id': illust_url.ugoira_id,
            }
        frame = ugoira_data['ugoira']['frames'][i]
        frame['md5'] = get_buffer_checksum(buffer)
        save_data['frames'].append(frame)
        combined_pixel_hash += get_pixel_hash(image)
        combined_size += len(buffer)
        result = create_data(buffer, os.path.join(working_directory, filename_join(str(i).zfill(6), file_ext)))
        if result is not None:
            retdata['errors'].append(_module_error('create_ugoira_post', result))
            return retdata
    retdata['md5'] = params['md5'] = get_buffer_checksum(encode_json(save_data).encode('utf'))
    if duplicate_check(params['md5']):
        retdata['duplicate'] = True
        return retdata
    error = _save_animation_file(working_directory, save_data)
    if error is not None:
        retdata['errors'].append(error)
        return retdata
    params['size'] = combined_size
    params['pixel_md5'] = get_buffer_checksum(combined_pixel_hash.encode('utf'))
    retdata['post'] = post = create_post_from_parameters(params, commit=False)
    create_directory(post.directory, isdir=True)
    try:
        os.rename(working_directory, post.frame_directory)
    except Exception as e:
        retdata['errors'].append(_module_error('create_ugoira_post', "Unable to rename directory: %s" % str(e)))
        return retdata
    # Only commit the post once the directory has been successfuly moved over
    commit_session()
    retdata['cleanup'] = False
    create_image_post_sample_preview_images(post, image)
    return retdata


def create_video_post(record, post_type, get_buffer, duplicate_check):
    retdata = _single_file_check(record, get_buffer, duplicate_check)
    if retdata['md5'] is None or retdata['duplicate']:
        return retdata
    illust_url = record.illust_url
    buffer = retdata['buffer']
    file_ext = check_filetype(buffer)
    if isinstance(file_ext, tuple):
        retdata['errors'].append(_module_error('create_video_post', file_ext[0]))
        file_ext = None
    if file_ext is None:
        file_ext = illust_url.url_extension
    md5 = get_buffer_checksum(buffer)
    temppost = Post(md5=md5, file_ext=file_ext)
    result = create_data(buffer, temppost.file_path)
    if result is not None:
        retdata['errors'].append(_module_error('create_video_post', result))
        return retdata
    info = get_video_info(temppost.file_path)
    if isinstance(info, str):
        retdata['errors'].append(_module_error('create_video_post', file_ext[0]))
        return retdata
    # From this point forward, the post will be created and all errors attached to that post
    params = merge_dicts(info, {
        'md5': md5,
        'size': len(buffer),
        'file_ext': file_ext,
        'type_name': post_type,
    })
    retdata['post'] = post = create_post_from_parameters(params)
    if (info['width'] != illust_url.width) or (info['height'] != illust_url.height):
        msg = "Mismatching image dimensions: Reported - %d x %d, Actual - %d x %d" %\
              (illust_url.width, illust_url.height, info['width'], info['height'])
        create_and_append_error(post, *_module_error('create_video_post', msg))
    create_video_post_sample_preview_images(post)
    return retdata


def update_video_post(post, buffer, illust_url):
    file_ext = check_filetype(buffer)
    if isinstance(file_ext, tuple):
        create_and_append_error(post, *_module_error('create_video_post', file_ext[0]))
        file_ext = None
    if file_ext is None:
        file_ext = illust_url.url_extension
    md5 = get_buffer_checksum(buffer)
    temppost = Post(md5=md5, file_ext=file_ext)
    result = create_data(buffer, temppost.file_path)
    if result is not None:
        create_and_append_error(post, *_module_error('create_video_post', result))
        return False
    info = get_video_info(temppost.file_path)
    if isinstance(info, str):
        create_and_append_error(post, *_module_error('create_video_post', file_ext[0]))
        return False
    params = merge_dicts(info, {
        'md5': md5,
        'size': len(buffer),
        'file_ext': file_ext,
    })
    update_post_from_parameters(post, params)
    if (info['width'] != illust_url.width) or (info['height'] != illust_url.height):
        msg = "Mismatching image dimensions: Reported - %d x %d, Actual - %d x %d" %\
              (illust_url.width, illust_url.height, info['width'], info['height'])
        create_and_append_error(post, *_module_error('create_video_post', msg))
    create_video_post_sample_preview_images(post)
    return True


def create_video_post_sample_preview_images(post):
    errors = []
    sample_buffer = None
    # Try to download the sample from the source first
    for illust_url in post.illust_urls:
        if illust_url.sample_url is None:
            continue
        results = download_illust_sample(illust_url)
        errors.extend(results['errors'])
        if results['buffer'] is not None:
            sample_buffer = results['buffer']
            break
    # Otherwise, try to create a sample from the video
    if sample_buffer is None:
        save_path = os.path.join(TEMP_DIRECTORY, post.md5 + '.' + 'jpg')
        error = create_video_screenshot(post.file_path, save_path)
        if error is None:
            sample_buffer = put_get_raw(save_path, 'rb')
        else:
            errors.append(error)
    if sample_buffer is not None:
        sample_image = _load_image(sample_buffer)
        if not isinstance(sample_image, tuple):
            error = create_sample(sample_image, post.sample_path, downsample=post.has_sample)
            if error is not None:
                errors.append(error)
            error = create_preview(sample_image, post.preview_path, downsample=post.has_preview)
            if error is not None:
                errors.append(error)
        else:
            errors.append(sample_image)
    create_and_extend_errors(post, errors)


def unlink_post_subscription_element(post):
    selectinload_batch_primary(post.illust_urls, 'subscription_element', reverse=True)
    for illust_url in post.illust_urls:
        element = illust_url.subscription_element
        if element is not None and element.status_name not in ['duplicate', 'unlinked']:
            update_subscription_element_from_parameters(element, {'status_name': 'unlinked', 'expires': None})


def redownload_post(post):
    post_illust_url = None
    buffer = None
    for illust_url in post.illust_urls:
        if illust_url.type == 'unknown':
            continue
        results = download_illust_url(illust_url)
        if results['buffer'] is not None:
            create_and_extend_errors(post, results['errors'])
            post_illust_url = illust_url
            buffer = results['buffer']
            break
    if post_illust_url is not None:
        if post_illust_url.type == 'image':
            return update_image_post(post, buffer, illust_url)
        success = update_video_post(post, buffer, illust_url)
        if success and post.is_video:
            create_video_sample_preview_files(post)
        return success
    else:
        create_and_append_error(post, *_module_error('redownload_post', "Unable to download from any illust URL"))
        return False


def download_post_frames(post):
    for illust_url in post.illust_urls:
        errors = []
        for i, buffer in enumerate(download_illust_url_frames(illust_url)):
            if isinstance(buffer, tuple):
                errors.append(buffer)
                continue
            result = create_data(buffer, post.frame(i))
            if result is not None:
                errors.append(_module_error('download_frames', result))
        if len(errors):
            create_and_extend_errors(post, errors)
        else:
            return True
    return False


def check_all_posts_for_danbooru_id():
    print("Checking all posts for Danbooru ID.")
    status = {'found': 0, 'notfound': 0}
    query = get_posts_to_query_danbooru_id_query()
    page = query.sequential_paginate(per_page=5000, page='newest_first')
    for posts in records_paginate('check_all_posts_for_danbooru_id', page):
        if not check_posts_for_danbooru_id(posts, status):
            break
    return status


def check_artist_posts_for_danbooru_id(artist_id):
    artist = Artist.find(artist_id)
    query = get_artist_posts_without_danbooru_ids_query(artist)
    page = query.sequential_paginate(per_page=100, page='newest_first', distinct=True)
    for posts in records_paginate('check_artist_posts_for_danbooru_id', page):
        if not check_posts_for_danbooru_id(posts, {}):
            break


def check_posts_for_danbooru_id(posts, status=None):
    status = status or {}
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
                    inc_dict_entry(status, 'notfound')
                    continue
                update_post_from_parameters(post, {'danbooru_id': danbooru_post['id']})
                inc_dict_entry(status, 'found')
    return True


def move_post_media_to_alternate(post, reverse=False):
    temppost = post.copy()
    alternate = not reverse
    if post.alternate == alternate:
        print_warning("%s already moved!" % post.shortlink)
        return
    temppost.alternate = alternate
    if post.is_ugoira:
        copy_directory(post.frame_directory, temppost.frame_directory, True)
    else:
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
    if post.is_ugoira:
        clear_directory(post.frame_directory)
    else:
        delete_file(temppost.file_path)
    if post.has_sample:
        delete_file(temppost.sample_path)
    if post.has_preview:
        delete_file(temppost.preview_path)
    if post.is_video:
        delete_file(temppost.video_sample_path)
        delete_file(temppost.video_preview_path)


def delete_post(post, retdata=None):
    """Hard delete. Continue as long as post record gets deleted."""

    def _delete(post):
        msg = "[%s]: deleted\n" % post.shortlink
        for pool_element in post.pool_elements:
            delete_pool_element(pool_element)
        delete_record(post)
        commit_session()
        print(msg)

    retdata = retdata or {'error': False, 'is_deleted': False}
    temppost = post.copy()
    retdata.update(delete_data(post, _delete))
    if retdata['error']:
        return retdata
    retdata['is_deleted'] = True
    error = _delete_media_files(temppost)
    if error is not None:
        return handle_error_message(error, retdata)
    return retdata


def archive_post_for_deletion(post, days_to_expire):
    """Soft delete. Preserve data at all costs."""
    retdata = {'error': False, 'is_deleted': False}
    retdata.update(save_post_to_archive(post, days_to_expire))
    if retdata['error']:
        return retdata
    return delete_post(post, retdata)


def save_post_to_archive(post, days_to_expire):
    retdata = {'error': False}
    archive = get_archive_by_post_md5(post.md5)
    if archive is None:
        archive = create_archive_from_parameters({'days': days_to_expire, 'type_name': 'post'}, commit=False)
    else:
        update_archive_from_parameters(archive, {'days': days_to_expire}, commit=False)
    retdata['item'] = archive.basic_json()
    archive_params = {k: v for (k, v) in post.basic_json().items() if k in ArchivePost.basic_attributes}
    archive_params['frames'] = post.frames
    archive_params['tags_json'] = list(post.tag_names)
    archive_params['errors_json'] = [{'module': error.module,
                                      'message': error.message,
                                      'created': error.created.isoformat()}
                                     for error in post.errors]
    archive_params['notations_json'] = [{'body': notation.body,
                                         'created': notation.created.isoformat(),
                                         'updated': notation.updated.isoformat()}
                                        for notation in post.notations]
    if archive.post_data is None:
        archive_params['archive_id'] = archive.id
        create_archive_post_from_parameters(archive_params)
    else:
        update_archive_post_from_parameters(archive.post_data, archive_params)
    error = _copy_media_files(post, archive.post_data, True, False)
    if error is not None:
        return handle_error_message(error, retdata)
    return retdata


def recreate_archived_post(archive):
    post_data = archive.post_data
    post = get_post_by_md5(post_data.md5)
    if post is not None:
        return handle_error_message(f"Post already exists: {post.shortlink}")
    post = create_post_from_parameters(post_data.recreate_json(), commit=False)
    error = _copy_media_files(post, post_data, False, True)
    if error is not None:
        SESSION.rollback()
        return handle_error_message(error)
    # Once the file move is successful, keep going even if there are errors.
    post.tag_names.extend(post_data.tags_json)
    for notation in post_data.notations_json:
        createparams = merge_dicts(notation, {'post_id': post.id})
        create_notation_from_parameters(createparams, commit=False)
    for error in post_data.errors_json:
        createparams = merge_dicts(error, {'post_id': post.id})
        create_error_from_parameters(createparams, commit=False)
    retdata = {'error': False, 'item': post.basic_json()}
    temppost = post.copy()
    commit_session()
    retdata.update(create_sample_preview_files(temppost))
    if temppost.is_video:
        create_video_sample_preview_files(temppost)
    SessionThread(target=process_image_matches, args=([temppost.id],)).start()
    update_archive_from_parameters(archive, {'days': 7})
    return retdata


def generate_missing_image_hashes(manual):
    total = 0
    max_batches = 10 if not manual else float('inf')
    query = missing_image_hashes_query()
    query = query.options(selectinload(Post.illust_urls).selectinload(IllustUrl.subscription_element),
                          selectinload(Post.image_hashes))
    page = query.sequential_paginate(per_page=20, page='newest_first')
    for posts in records_paginate('generate_missing_image_hashes', page, max_batches):
        for post in posts:
            generate_post_image_hashes(post)
            if post.active_subscription_element is None:
                generate_similarity_matches(post)
            total += 1
        commit_session()
    return total


def calculate_similarity_matches(manual):
    total = 0
    max_batches = 10 if not manual else float('inf')
    query = missing_similarity_matches_query()
    query = query.options(selectinload(Post.image_hashes))
    page = query.sequential_paginate(per_page=50, page='newest_first')
    for posts in records_paginate('calculate_similarity_matches', page, max_batches):
        for post in posts:
            generate_similarity_matches(post)
            total += 1
        commit_session()
    return total


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


def create_video_sample_preview_files(post, video_sample=True):
    convert_mp4_to_webp(post.file_path, post.video_preview_path)
    if video_sample:
        convert_mp4_to_webm(post.file_path, post.video_sample_path)


def relocate_old_posts_to_alternate(manual):
    if ALTERNATE_MOVE_DAYS is None:
        return
    moved = 0
    max_batches = RELOCATE_PAGE_LIMIT if not manual else float('inf')
    query = alternate_posts_query(ALTERNATE_MOVE_DAYS)
    page = query.sequential_paginate(per_page=50, page='oldest_first')
    for posts in records_paginate('relocate_old_posts_to_alternate', page, max_batches):
        for post in posts:
            print(f"Moving {post.shortlink}")
            move_post_media_to_alternate(post)
            moved += 1
    return moved


def process_image_matches(post_ids):
    printer = buffered_print("Process Image Matches")
    posts = get_posts_by_id(post_ids)
    for post in posts:
        generate_post_image_hashes(post, printer=printer)
        generate_similarity_matches(post, printer=printer)
    SESSION.commit()
    printer.print()


# #### Private functions

def _single_file_check(record, get_buffer, duplicate_check):
    retdata = get_buffer(record)
    if retdata['buffer'] is None:
        retdata['md5'] = None
        return retdata
    retdata['md5'] = get_buffer_checksum(retdata['buffer'])
    retdata['duplicate'] = duplicate_check(retdata['md5'])
    return retdata


def _save_animation_file(working_directory, save_data):
    print("Saving animation file.")
    try:
        put_get_json(os.path.join(working_directory, 'animation.json'), 'w', save_data)
    except Exception as e:
        return _module_error('save_animation_file', "Unable to save animation file: %s" % str(e))


def _copy_media_files(post, archive_post, copy_preview, reverse):
    from_item, to_item = (post, archive_post) if not reverse else (archive_post, post)
    create_directory(to_item.file_path)
    try:
        if post.is_ugoira:
            print(f"Copying directory:\n\t{from_item.frame_directory}\n\t-> {to_item.frame_directory}")
            copy_directory(from_item.frame_directory, to_item.frame_directory, True)
        else:
            print(f"Copying file:\n\t{from_item.file_path}\n\t-> {to_item.file_path}")
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
        'file': post.file_path if not post.is_ugoira else None,
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
    if post.is_ugoira:
        print("Clearing frame directory:", post.frame_directory)
        try:
            clear_directory(post.frame_directory)
        except Exception as e:
            error_messages.append(f"Error clearing directory: {str(e)}")
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
        source = illust_url.source
        download_url = source.get_sample_url(illust_url)
        print("Downloading", download_url)
        buffer = get_http_data(download_url, headers=source.IMAGE_HEADERS)
        if isinstance(buffer, str):
            create_and_append_error(post, 'post_rec.get_video_thumb_binary',
                                    "Download URL: %s => %s" % (download_url, buffer))
            continue
        return buffer


def _load_image(buffer):
    image = load_image(buffer)
    if isinstance(image, str):
        return _module_error('load_image', image)
    try:
        if check_alpha(image):
            return convert_alpha(image)
        else:
            return image
    except Exception as e:
        return _module_error('load_image', "Error removing alpha transparency: %s" % repr(e))


def _module_error(function, message):
    return (f'post_rec.{function}', message)
