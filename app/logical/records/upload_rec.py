# APP/LOGICAL/RECORDS/UPLOAD_REC.PY

# ## PYTHON IMPORTS
import itertools

# ## PACKAGE IMPORTS
from utility.time import minutes_ago, days_ago
from utility.data import add_dict_entry
from utility.file import no_file_extension
from utility.uprint import buffered_print, print_warning

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Upload
from ..utility import unique_objects, SessionThread
from ..sources.base_src import get_post_source
from ..database.base_db import safe_db_execute
from ..database.illust_db import get_site_illust, get_site_illusts
from ..database.upload_db import update_upload_from_parameters
from ..database.upload_element_db import create_upload_element_from_parameters, update_upload_element_from_parameters
from ..database.post_db import get_posts_by_id
from ..database.error_db import create_and_append_error
from ..media import convert_mp4_to_webp, convert_mp4_to_webm
from ..downloader.file_dl import convert_file_upload
from .artist_rec import update_artist_from_source, check_artists_for_boorus
from .illust_rec import create_illust_from_source, update_illust_from_source
from .media_asset_rec import download_media_asset, move_media_asset
from .post_rec import check_posts_for_danbooru_id, create_post_record
from .image_hash_rec import generate_post_image_hashes
from .similarity_match_rec import generate_similarity_matches

# ## FUNCTIONS

# #### Upload functions


def process_upload(upload_id):
    printer = buffered_print("Process Upload")
    upload = None

    def try_func(scope_vars):
        nonlocal upload
        upload = Upload.find(upload_id)
        printer("Upload:", upload.id)
        update_upload_from_parameters(upload, {'status': 'processing'})
        if upload.request_url is not None:
            process_network_upload(upload)
        elif upload.illust_url_id is not None and upload.media_filepath is not None:
            process_file_upload(upload)
        else:
            raise Exception(f"Missing values on {upload.shortlink}.")

    def msg_func(scope_vars, e):
        return f"Unhandled exception occurred on upload #{upload_id}: {repr(e)}"

    def error_func(scope_vars, e):
        nonlocal upload
        upload = upload or Upload.find(upload_id)
        update_upload_from_parameters(upload, {'status': 'error'})

    def finally_func(scope_vars, error, data):
        nonlocal upload
        upload = upload or Upload.find(upload_id)
        printer("Upload:", upload.status)
        printer("Total:", len(upload.posts))
        printer("Complete:", len(upload.complete_posts))
        printer("Duplicate:", len(upload.duplicate_posts))
        if upload.status.name == 'complete' and len(upload.complete_posts) > 0:
            printer("Starting secondary threads.")
            post_ids = upload.complete_post_ids
            SessionThread(target=process_image_matches, args=(post_ids,)).start()
            SessionThread(target=check_for_matching_danbooru_posts, args=(post_ids,)).start()
            SessionThread(target=check_for_new_artist_boorus, args=(post_ids,)).start()
            video_post_ids = [post.id for post in upload.complete_posts if post.media.is_video]
            if len(video_post_ids):
                SessionThread(target=process_videos, args=(video_post_ids,)).start()

    safe_db_execute('process_upload', 'records.upload_rec',
                    try_func=try_func, msg_func=msg_func, printer=printer,
                    error_func=error_func, finally_func=finally_func)
    printer.print()
    SESSION.remove()


# #### Network uploads

def process_network_upload(upload):
    # Request URL should have already been validated, so no null test needed
    source = get_post_source(upload.request_url)
    site_illust_id = source.get_illust_id(upload.request_url)
    error = source.source_prework(site_illust_id)
    if error is not None:
        append_error(upload, error)
    requery_time = days_ago(1)
    illust = get_site_illust(site_illust_id, source.SITE.id)
    if illust is None:
        illust = create_illust_from_source(site_illust_id, source)
        if illust is None:
            create_and_append_error('upload_rec.process_network_upload',
                                    "Unable to create illust: %s" % (source.ILLUST_SHORTLINK % site_illust_id),
                                    commit=False)
            update_upload_from_parameters(upload, {'status': 'error'}, commit=True)
            return
    elif illust.updated < requery_time:
        update_illust_from_source(illust)
    # The artist will have already been created in the create illust step if it didn't exist
    if illust.artist.updated < requery_time:
        update_artist_from_source(illust.artist)
    if source.is_image_url(upload.request_url):
        process_network_single_upload(upload, illust)
    else:
        process_network_multi_upload(upload, illust)
    update_upload_from_parameters(upload, {'status': 'complete'}, commit=True)


def process_network_single_upload(upload, illust):
    if len(upload.elements) == 0:
        normalized_request_url = no_file_extension(illust.source.partial_media_url(upload.request_url))
        illust_url = next((illust_url for illust_url in illust.urls
                           if no_file_extension(illust_url.url) == normalized_request_url),
                          None)
        if illust_url is None:
            create_and_append_error('upload_rec.process_network_single_upload',
                                    "Unable to find illust URL: %s -> %s" %
                                    (upload.request_url, illust.shortlink),
                                    commit=True)
            update_upload_from_parameters(upload, {'status': 'error'}, commit=True)
            return
        params = {
            'upload_id': upload.id,
            'illust_url_id': illust_url.id,
        }
        element = create_upload_element_from_parameters(params, commit=True)
        process_network_upload_element(element)
    elif upload.elements[0].status.name == 'pending':
        process_network_upload_element(upload.elements[0])


def process_network_multi_upload(upload, illust):
    all_upload_urls = [no_file_extension(illust.source.partial_media_url(upload_url.url))
                       for upload_url in upload.image_urls]
    upload_elements = upload.elements
    total = 0
    for illust_url in illust.urls:
        normalized_illust_url = no_file_extension(illust_url.url)
        if (len(all_upload_urls) > 0) and (normalized_illust_url not in all_upload_urls):
            continue
        element = next((element for element in upload_elements if element.illust_url_id == illust_url.id), None)
        if element is None:
            params = {
                'upload_id': upload.id,
                'illust_url_id': illust_url.id,
            }
            element = create_upload_element_from_parameters(params, commit=True)
        if element.status.name == 'pending':
            process_network_upload_element(element)
        total += 1
    if len(all_upload_urls) > 0 and len(all_upload_urls) != total:
        create_and_append_error('upload_rec.process_network_multi_upload',
                                "Did not find all upload URLS in illust: expected (%d) : found (%d)" %
                                (len(upload.image_urls), total),
                                commit=False)


def process_network_upload_element(element):
    illust_url = element.illust_url
    source = illust_url.source
    download_url = illust_url.full_original_url
    alternate_url = illust_url.full_alternate_url
    results = download_media_asset(download_url, source, 'primary', alternate_url=alternate_url)
    for error in results['errors']:
        create_and_append_error(element, *error, commit=False)
    if results['media_asset'] is not None:
        params = {
            'media_asset_id': results['media_asset'].id,
        }
        if results['media_asset'].post is None:
            if results['media_asset'].location.name != 'primary':
                result = move_media_asset(results['media_asset'], 'primary')
                if isinstance(result, str):
                    create_and_append_error(element, 'upload_rec.process_network_upload_element', result, commit=False)
                    update_upload_element_from_parameters(element, {'status': 'error'}, commit=True)
                    return
            create_post_record(element, results['media_asset'])
            params['status'] = 'complete'
        else:
            params['status'] = 'duplicate'
        update_upload_element_from_parameters(element, params, commit=True)
    else:
        update_upload_element_from_parameters(element, {'status': 'error'}, commit=True)


# #### File upload

def process_file_upload(upload):
    illust = upload.file_illust_url.illust
    requery_time = days_ago(1)
    if illust.updated < requery_time:
        update_illust_from_source(illust)
    if illust.artist.updated < requery_time:
        update_artist_from_source(illust.artist)
    if convert_file_upload(upload):
        update_upload_from_parameters(upload, {'status': 'complete'})
    else:
        update_upload_from_parameters(upload, {'status': 'error'})


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
