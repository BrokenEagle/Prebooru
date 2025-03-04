# APP/LOGICAL/RECORDS/UPLOAD_REC.PY

# ## PYTHON IMPORTS
import itertools

# ## PACKAGE IMPORTS
from utility.time import minutes_ago, days_ago
from utility.uprint import buffered_print
from utility.data import get_buffer_checksum
from utility.file import put_get_raw

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Upload
from ..utility import unique_objects, SessionThread
from ..records.artist_rec import update_artist_from_source, check_artists_for_boorus
from ..records.illust_rec import update_illust_from_source
from ..records.post_rec import check_posts_for_danbooru_id
from ..records.image_hash_rec import generate_post_image_hashes
from ..records.similarity_match_rec import generate_similarity_matches
from ..database.base_db import safe_db_execute
from ..database.upload_db import update_upload_from_parameters
from ..database.post_db import update_post_from_parameters, get_posts_by_id, get_post_by_md5
from ..database.illust_url_db import update_illust_url_from_parameters
from ..database.error_db import create_and_extend_errors
from ..media import convert_mp4_to_webp, convert_mp4_to_webm
from .post_rec import create_image_post, create_video_post


# ## FUNCTIONS

# #### Upload functions

def process_upload(upload_id):
    printer = buffered_print("Process Upload")
    upload = None

    def try_func(scope_vars):
        nonlocal upload
        upload = Upload.find(upload_id)
        printer("Upload:", upload.id)
        update_upload_from_parameters(upload, {'status_name': 'processing'})
        if upload.illust_url_id is not None and upload.media_filepath is not None:
            process_file_upload(upload)
        else:
            raise Exception(f"Missing values on {upload.shortlink}.")

    def msg_func(scope_vars, e):
        return f"Unhandled exception occurred on upload #{upload_id}: {repr(e)}"

    def error_func(scope_vars, e):
        nonlocal upload
        upload = upload or Upload.find(upload_id)
        update_upload_from_parameters(upload, {'status_name': 'error'})

    def finally_func(scope_vars, error, data):
        nonlocal upload
        upload = upload or Upload.find(upload_id)
        printer("Upload:", upload.status)
        if upload.status_name == 'complete':
            printer("Starting secondary threads.")
            post_ids = [upload.illust_url.post_id]
            SessionThread(target=process_image_matches, args=(post_ids,)).start()
            if upload.artist.primary:
                SessionThread(target=check_for_matching_danbooru_posts, args=(post_ids,)).start()
                SessionThread(target=check_for_new_artist_boorus, args=(post_ids,)).start()
            if upload.post.is_video:
                SessionThread(target=process_videos, args=(post_ids,)).start()

    safe_db_execute('process_upload', 'records.upload_rec',
                    try_func=try_func, msg_func=msg_func, printer=printer,
                    error_func=error_func, finally_func=finally_func)
    printer.print()
    SESSION.remove()


def process_file_upload(upload):
    illust = upload.illust
    requery_time = days_ago(1)
    if illust.updated < requery_time:
        update_illust_from_source(illust)
    if illust.artist.updated < requery_time:
        update_artist_from_source(illust.artist)
    create_post_from_upload(upload)


def create_post_from_upload(upload):
    illust_url = upload.illust_url
    if illust_url.type == 'unknown':
        raise Exception("Unable to create post for unknown illust URL type")
    if illust_url.post_id is not None:
        update_upload_from_parameters(upload, {'status_name': 'duplicate'})
        if illust_url.post.type_name != 'user':
            update_post_from_parameters(illust_url.post, {'type_name': 'user'})
        return
    buffer = put_get_raw(upload.media_filepath, 'rb')
    md5 = get_buffer_checksum(buffer)
    update_illust_url_from_parameters(illust_url, {'md5': md5})
    post = get_post_by_md5(md5)
    if post is not None:
        update_illust_url_from_parameters(illust_url, {'post_id': post.id})
        update_upload_from_parameters(upload, {'status_name': 'duplicate'})
        if post.type_name != 'user':
            update_post_from_parameters(post, {'type_name': 'user'})
        return
    if illust_url.type == 'image':
        results = create_image_post(buffer, illust_url, 'user')
    else:
        results = create_video_post(buffer, illust_url, 'user')
    create_and_extend_errors(upload, results['errors'])
    if results['post'] is None:
        update_upload_from_parameters(upload, {'status_name': 'error'})
    else:
        update_upload_from_parameters(upload, {'status_name': 'complete'})


# #### Secondary task functions

def process_image_matches(post_ids):
    printer = buffered_print("Process Image Matches")
    posts = get_posts_by_id(post_ids)
    for post in posts:
        generate_post_image_hashes(post, printer=printer)
        generate_similarity_matches(post, printer=printer)
    SESSION.commit()
    printer.print()


def process_videos(post_ids):
    printer = buffered_print("Process Videos")
    posts = get_posts_by_id(post_ids)
    printer("Videos to process:", len(posts))
    mp4_count = 0
    for post in posts:
        if post.file_ext == 'mp4':
            convert_mp4_to_webp(post.file_path, post.video_preview_path)
            convert_mp4_to_webm(post.file_path, post.video_sample_path)
            mp4_count += 1
    printer(f"MP4s processed: {mp4_count}")
    printer.print()


def check_for_matching_danbooru_posts(post_ids):
    printer = buffered_print("Check Danbooru Posts")
    printer("Posts to check:", len(post_ids))
    posts = get_posts_by_id(post_ids)
    check_posts_for_danbooru_id(posts)
    printer.print()


def check_for_new_artist_boorus(post_ids):
    printer = buffered_print("Check Artist Boorus")
    posts = get_posts_by_id(post_ids)
    all_artists = unique_objects([*itertools.chain(*[post.artists for post in posts])])
    check_artists = [artist for artist in all_artists if artist.created > minutes_ago(1)]
    printer("Artists to check:", len(check_artists))
    if len(check_artists):
        check_artists_for_boorus(check_artists)
    printer.print()
