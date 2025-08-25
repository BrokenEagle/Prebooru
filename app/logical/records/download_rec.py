# APP/LOGICAL/RECORDS/DOWNLOAD_REC.PY

# ## PYTHON IMPORTS
import itertools

# ## PACKAGE IMPORTS
from utility.time import minutes_ago, days_ago
from utility.file import no_file_extension
from utility.uprint import buffered_print

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Download
from ..utility import unique_objects, SessionThread, set_error
from ..sources.base_src import get_post_source
from ..records.artist_rec import update_artist_from_source, check_artists_for_boorus
from ..records.illust_rec import create_illust_from_source, update_illust_from_source
from ..records.post_rec import check_posts_for_danbooru_id
from ..records.image_hash_rec import generate_post_image_hashes
from ..records.similarity_match_rec import generate_similarity_matches
from ..database.base_db import safe_db_execute
from ..database.illust_db import get_site_illust
from ..database.illust_url_db import update_illust_url_from_parameters
from ..database.download_db import create_download_from_parameters, update_download_from_parameters,\
    get_download_by_request_url
from ..database.download_element_db import create_download_element_from_parameters,\
    update_download_element_from_parameters, get_download_element
from ..database.post_db import get_posts_by_id, get_post_by_md5, update_post_from_parameters
from ..database.error_db import create_and_extend_errors, create_and_append_error, append_error
from ..media import convert_mp4_to_webp, convert_mp4_to_webm
from .post_rec import create_image_post, create_video_post, create_ugoira_post


# ## FUNCTIONS

# #### Download functions

def process_download(download_id):
    printer = buffered_print("Process Download")
    download = None

    def try_func(scope_vars):
        nonlocal download
        download = Download.find(download_id)
        printer("Download:", download.id)
        update_download_from_parameters(download, {'status_name': 'processing'})
        process_network_download(download)

    def msg_func(scope_vars, e):
        return f"Unhandled exception occurred on download #{download_id}: {repr(e)}"

    def error_func(scope_vars, e):
        nonlocal download
        download = download or Download.find(download_id)
        update_download_from_parameters(download, {'status_name': 'error'})

    def finally_func(scope_vars, error, data):
        nonlocal download
        download = download or Download.find(download_id)
        printer("Download:", download.status)
        printer("Total:", len(download.posts))
        printer("Complete:", len(download.complete_posts))
        printer("Duplicate:", len(download.duplicate_posts))
        if download.status_name == 'complete' and len(download.complete_posts) > 0:
            printer("Starting secondary threads.")
            post_ids = download.complete_post_ids
            SessionThread(target=process_image_matches, args=(post_ids, download.artist.primary)).start()
            if download.artist.primary:
                SessionThread(target=check_for_matching_danbooru_posts, args=(post_ids,)).start()
                SessionThread(target=check_for_new_artist_boorus, args=(post_ids,)).start()
            video_post_ids = [post.id for post in download.complete_posts if post.is_video]
            if len(video_post_ids):
                SessionThread(target=process_videos, args=(video_post_ids,)).start()

    safe_db_execute('process_download', 'records.download_rec',
                    try_func=try_func, msg_func=msg_func, printer=printer,
                    error_func=error_func, finally_func=finally_func)
    printer.print()
    SESSION.remove()


# #### Auxiliary functions

def process_network_download(download):
    illust = _create_download_illust(download)
    source = illust.source
    all_download_urls = [no_file_extension(source.normalize_image_url(download_url.url))
                         for download_url in download.image_urls]
    download_elements = download.elements
    image_download = source.is_image_url(download.request_url)
    normalized_request_url =\
        no_file_extension(source.normalize_image_url(download.request_url))\
        if image_download\
        else None
    for illust_url in illust.urls:
        normalized_illust_url = no_file_extension(illust_url.url)
        if image_download and normalized_request_url != normalized_illust_url:
            continue
        elif (len(all_download_urls) > 0) and (normalized_illust_url not in all_download_urls):
            continue
        element = next((element for element in download_elements if element.illust_url_id == illust_url.id), None)
        if element is None:
            params = {
                'download_id': download.id,
                'illust_url_id': illust_url.id,
            }
            element = create_download_element_from_parameters(params)
        create_post_from_download_element(element)
        if image_download:
            break
    update_download_from_parameters(download, {'status_name': 'complete'})


def create_post_from_download_element(element):
    illust_url = element.illust_url
    if illust_url.post is not None:
        update_download_element_from_parameters(element, {'status_name': 'duplicate'})
        if illust_url.post.type_name != 'user':
            update_post_from_parameters(illust_url.post, {'type_name': 'user'})
        return
    if illust_url.type == 'image':
        results = create_image_post(illust_url, 'user', _duplicate_check)
    elif illust_url.type == 'video':
        results = create_video_post(illust_url, 'user', _duplicate_check)
    elif illust_url.type == 'ugoira':
        results = create_ugoira_post(illust_url, 'user', _duplicate_check)
    else:
        raise Exception("Unable to create post for unknown illust URL type")
    create_and_extend_errors(element, results['errors'])
    if results['md5'] is None:
        update_download_element_from_parameters(element, {'status_name': 'error'})
        return
    update_illust_url_from_parameters(illust_url, {'md5': results['md5']})
    if results['duplicate']:
        update_download_element_from_parameters(element, {'status_name': 'duplicate'})
        if results['post'].type_name != 'user':
            update_post_from_parameters(results['post'], {'type_name': 'user'})
        return
    if results['post'] is None:
        update_download_element_from_parameters(element, {'status_name': 'error'})
    else:
        update_download_element_from_parameters(element, {'status_name': 'complete'})


def create_download_from_illust_url(illust_url):
    illust = illust_url.illust
    illust_key = '%s-%d' % (illust.site_name, illust.site_illust_id)
    illust_download = get_download_by_request_url(illust_key)
    if illust_download is None:
        illust_download = create_download_from_parameters({'request_url': illust_key, 'status_name': 'processing'})
    else:
        update_download_from_parameters(illust_download, {'status_name': 'processing'})
    illust_url_element = get_download_element(illust_download.id, illust_url.id)
    if illust_url_element is None:
        params = {
            'download_id': illust_download.id,
            'illust_url_id': illust_url.id,
        }
        illust_url_element = create_download_element_from_parameters(params)
    else:
        update_download_element_from_parameters(illust_url_element, {'status_name': 'pending'})
    create_post_from_download_element(illust_url_element)
    retdata = {'error': False}
    if illust_url_element.status_name == 'complete':
        update_download_from_parameters(illust_download, {'status_name': 'complete'})
    else:
        # Setting the unknown status so that it can't be restarted from the download UI
        update_download_from_parameters(illust_download, {'status_name': 'unknown'})
        retdata = set_error(retdata, "Error downloading post on %s." % illust_url_element.shortlink)
    return retdata


# #### Secondary task functions

def process_image_matches(post_ids, primary):
    printer = buffered_print("Process Image Matches")
    posts = get_posts_by_id(post_ids)
    for post in posts:
        generate_post_image_hashes(post, printer=printer)
        if primary:
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


# ## Private

def _duplicate_check(md5):
    post = get_post_by_md5(md5)
    return post is not None


def _create_download_illust(download):
    # Request URL should have already been validated, so no null test needed
    source = get_post_source(download.request_url)
    site_illust_id = source.get_illust_id(download.request_url)
    error = source.source_prework(site_illust_id)
    if error is not None:
        append_error(download, error)
    requery_time = days_ago(1)
    illust = get_site_illust(site_illust_id, source.SITE.id)
    if illust is None:
        illust = create_illust_from_source(site_illust_id, source)
        if illust is None:
            update_download_from_parameters(download, {'status_name': 'error'})
            create_and_append_error(download, 'download_rec.process_network_download',
                                    "Unable to create illust: %s" % (source.ILLUST_SHORTLINK % site_illust_id))
            return
    elif illust.updated < requery_time:
        update_illust_from_source(illust)
    # The artist will have already been created in the create illust step if it didn't exist
    if illust.artist.updated < requery_time:
        update_artist_from_source(illust.artist)
    return illust
