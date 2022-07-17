# APP/LOGICAL/RECORDS/ARCHIVE_DATA_REC.PY

# ### PYTHON IMPORTS
import os

# ### PACKAGE IMPORTS
from config import MEDIA_DIRECTORY, ALTERNATE_MOVE_DAYS
from utility.file import create_directory, put_get_raw, copy_file, delete_file, move_file

# ### LOCAL IMPORTS
from ... import SESSION
from ..utility import set_error
from ..media import load_image, create_sample, create_preview, create_video_screenshot
from ..database.post_db import create_post_from_raw_parameters, delete_post, post_append_illust_url, get_post_by_md5,\
    set_post_alternate, alternate_posts_query, copy_post
from ..database.illust_url_db import get_illust_url_by_url
from ..database.notation_db import create_notation_from_raw_parameters
from ..database.error_db import create_error_from_raw_parameters
from ..database.archive_data_db import get_archive_data, create_archive_data, update_archive_data,\
    ARCHIVE_DATA_DIRECTORY


# ## GLOBAL VARIABLES

TEMP_DIRECTORY = os.path.join(MEDIA_DIRECTORY, 'temp')


# ## FUNCTIONS

def move_post_media_to_alternate(post):
    temppost = copy_post(post)
    temppost.alternate = True
    copy_file(post.file_path, temppost.file_path, True)
    if post.has_sample:
        copy_file(post.sample_path, temppost.sample_path)
    if post.has_preview:
        copy_file(post.preview_path, temppost.preview_path)
    # Commit post as alternate location at this point since the files have been safely copied over
    set_post_alternate(post, True)
    # Any errors after this point will just leave orphan images, which can always be cleaned up later
    temppost.alternate = False
    delete_file(temppost.file_path)
    if post.has_sample:
        delete_file(temppost.sample_path)
    if post.has_preview:
        delete_file(temppost.preview_path)


def delete_post_and_media(post):
    """Hard delete. Continue as long as post record gets deleted."""
    retdata = {'error': False, 'is_deleted': False}
    file_path = post.file_path
    sample_path = post.sample_path if post.has_sample else None
    preview_path = post.preview_path if post.has_preview else None
    retdata = _delete_post_data(post, retdata)
    if retdata['error']:
        return retdata
    retdata = _delete_media_files(sample_path, preview_path, retdata, file_path=file_path)
    if not retdata['error']:
        retdata['is_deleted'] = True
    return retdata


def archive_post_for_deletion(post, expires):
    """Soft delete. Preserve data at all costs."""
    retdata = {'error': False, 'is_deleted': False}
    sample_path = post.sample_path if post.has_sample else None
    preview_path = post.preview_path if post.has_preview else None
    retdata = _archive_post_data(post, retdata, expires)
    if retdata['error']:
        return retdata
    retdata = _move_post_file(post, retdata)
    if retdata['error']:
        return retdata
    retdata['is_deleted'] = True
    retdata = _delete_post_data(post, retdata)
    if retdata['error']:
        return retdata
    return _delete_media_files(sample_path, preview_path, retdata)


def reinstantiate_archived_post(data):
    retdata = {'error': False}
    post = get_post_by_md5(data['body']['md5'])
    if post is not None:
        return set_error(retdata, "Post with MD5 %s already exists: post #%d" % (post.md5, post.id))
    try:
        post = create_post_from_raw_parameters(data['body'])
    except Exception as e:
        return set_error(retdata, "Error creating post: %s" % str(e))
    retdata = _move_post_file(post, retdata, True)
    if retdata['error']:
        return retdata
    retdata['item'] = post.to_json()
    # Once the file move is successful, keep going even if there are errors.
    create_sample_preview_files(post, retdata)
    relink_archived_post(data, post)
    for notation_data in data['relations']['notations']:
        notation = create_notation_from_raw_parameters(notation_data)
        post.notations.append(notation)
        SESSION.commit()
    for error_data in data['relations']['errors']:
        error = create_error_from_raw_parameters(error_data)
        post.errors.append(error)
        SESSION.commit()
    return retdata


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


def relink_archived_post(data, post=None):
    if post is None:
        post = get_post_by_md5(data['body']['md5'])
        if post is None:
            return "No post found with MD5 %s" % data['body']['md5']
    for link_data in data['links']['illusts']:
        illust_url = get_illust_url_by_url(site_id=link_data['site_id'], partial_url=link_data['url'])
        if illust_url is not None:
            post_append_illust_url(post, illust_url)


def relocate_old_posts_to_alternate():
    if ALTERNATE_MOVE_DAYS is None:
        return
    query = alternate_posts_query(ALTERNATE_MOVE_DAYS)
    page = query.limit_paginate(per_page=100)
    while True:
        print(f"relocate_old_posts_to_alternate: {page.first} - {page.last} / Total({page.count})")
        for post in page.items:
            print(f"Moving {post.shortlink}")
            move_post_media_to_alternate(post)
        if not page.has_next:
            return page.count
        page = page.next()


# #### Private functions

def _archive_post_data(post, retdata, expires):
    data = {
        'body': post.column_dict(),
        'scalars': {},
        'relations': {
            'notations': [notation.column_dict() for notation in post.notations],
            'errors': [error.column_dict() for error in post.errors],
        },
        'links': {
            'illusts': [{'url': illust_url.url, 'site_id': illust_url.site_id} for illust_url in post.illust_urls],
        },
    }
    archive_data = get_archive_data('post', post.md5)
    try:
        if archive_data is None:
            create_archive_data('post', post.md5, data, expires)
        else:
            update_archive_data(archive_data, data, expires)
    except Exception as e:
        return set_error(retdata, "Error archiving data: %s" % str(e))
    return retdata


def _move_post_file(post, retdata, reverse=False):
    archive_path = os.path.join(ARCHIVE_DATA_DIRECTORY, post.md5 + '.' + post.file_ext)
    to_path, from_path = (archive_path, post.file_path) if not reverse else (post.file_path, archive_path)
    create_directory(archive_path)
    try:
        move_file(from_path, to_path)
    except Exception as e:
        return set_error(retdata, "Error moving post file: %s" % str(e))
    return retdata


def _delete_post_data(post, retdata):
    try:
        delete_post(post)
    except Exception as e:
        SESSION.rollback()
        return set_error(retdata, "Error deleting post: %s" % str(e))
    return retdata


def _delete_media_files(sample_path, preview_path, retdata, file_path=None):
    print('_delete_media_files', file_path, sample_path, preview_path)
    media_paths = {
        'file': file_path,
        'sample': sample_path,
        'preview': preview_path,
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
