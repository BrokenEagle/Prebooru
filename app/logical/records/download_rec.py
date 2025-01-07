# APP/LOGICAL/RECORDS/DOWNLOAD_REC.PY

# ## PYTHON IMPORTS
import itertools

# ## PACKAGE IMPORTS
from utility.time import minutes_ago, days_ago
from utility.data import add_dict_entry, get_buffer_checksum
from utility.file import no_file_extension
from utility.uprint import buffered_print, print_warning

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Download, Illust
from ..utility import unique_objects, SessionThread
from ..sources.base_src import get_post_source
from ..records.artist_rec import update_artist_from_source, check_artists_for_boorus
from ..records.illust_rec import create_illust_from_source, update_illust_from_source
from ..records.post_rec import check_posts_for_danbooru_id
from ..records.image_hash_rec import generate_post_image_hashes
from ..records.similarity_match_rec import generate_similarity_matches
from ..database.base_db import safe_db_execute
from ..database.illust_db import get_site_illust, get_site_illusts
from ..database.illust_url_db import update_illust_url_from_parameters
from ..database.download_db import update_download_from_parameters
from ..database.download_element_db import create_download_element_from_parameters,\
    update_download_element_from_parameters
from ..database.post_db import get_posts_by_id, update_post_from_parameters, get_post_by_md5
from ..database.error_db import create_and_extend_errors, create_and_append_error, append_error
from ..media import convert_mp4_to_webp, convert_mp4_to_webm
from .illust_rec import download_illust_url
from .post_rec import create_image_post, create_video_post


# ## FUNCTIONS

# #### Download functions

def process_download(download_id):
    printer = buffered_print("Process Download")
    download = None

    def try_func(scope_vars):
        nonlocal download
        download = Download.find(download_id)
        printer("Download:", download.id)
        update_download_from_parameters(download, {'status': 'processing'})
        process_network_download(download)

    def msg_func(scope_vars, e):
        return f"Unhandled exception occurred on download #{download_id}: {repr(e)}"

    def error_func(scope_vars, e):
        nonlocal download
        download = download or Download.find(download_id)
        update_download_from_parameters(download, {'status': 'error'})

    def finally_func(scope_vars, error, data):
        nonlocal download
        download = download or Download.find(download_id)
        printer("Download:", download.status)
        printer("Total:", len(download.posts))
        printer("Complete:", len(download.complete_posts))
        printer("Duplicate:", len(download.duplicate_posts))
        if download.status.name == 'complete' and len(download.complete_posts) > 0:
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


# #### Element functions

def populate_download_elements(download, illust=None):
    if illust is None:
        source = get_post_source(download.request_url)
        site_illust_id = source.get_illust_id(download.request_url)
        illust = get_site_illust(site_illust_id, source.site.id)
        if illust is None:
            return
    else:
        source = illust.site.source
    all_download_urls = [source.normalize_image_url(download_url.url) for download_url in download.image_urls]
    download_elements = list(download.elements)
    for illust_url in illust.urls:
        if (len(all_download_urls) > 0) and (illust_url.url not in all_download_urls):
            continue
        element = next((element for element in download_elements if element.illust_url_id == illust_url.id), None)
        if element is None:
            params = {
                'download_id': download.id,
                'illust_url_id': illust_url.id,
            }
            element = create_download_element_from_parameters(params, commit=False)
            download_elements.append(element)
    return download_elements


def populate_all_download_elements(downloads):
    illust_lookup = {}
    illust_index = {}
    download_elements = {}
    for download in downloads:
        source = download._source
        if download.request_url is not None:
            site_illust_id = source.get_illust_id(download.request_url)
        elif download.illust_url_id is not None:
            site_illust_id = download.illust_url.illust.site_illust_id
        else:
            print_warning(f"Unable to find an illust for {download.shortlink}")
            continue
        add_dict_entry(illust_lookup, source.SITE.id, site_illust_id)
        illust_index[download.id] = {'site_id': source.SITE.id, 'site_illust_id': site_illust_id}
    illusts = []
    for key in illust_lookup:
        illusts += get_site_illusts(key, illust_lookup[key], load_urls=True)
    for download in downloads:
        illust_params = illust_index[download.id]
        illust = next((illust for illust in illusts
                       if illust.site_id == illust_params['site_id']
                       and illust.site_illust_id == illust_params['site_illust_id']), None)
        if illust is None:
            continue
        download_elements[download.id] = populate_download_elements(download, illust=illust)
    return download_elements


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
    update_download_from_parameters(download, {'status': 'complete'})


def create_post_from_download_element(element):
    illust_url = element.illust_url
    if illust_url.type == 'unknown':
        raise Exception("Unable to create post for unknown illust URL type")
    if illust_url.post_id is not None:
        params = {
            'status': 'duplicate',
            'md5': illust_url.post.md5,
        }
        update_download_element_from_parameters(element, params)
        if illust_url.post.type_name != 'user':
            update_post_from_parameters(illust_url.post, {'type': 'user'})
        return
    results = download_illust_url(illust_url)
    create_and_extend_errors(element, results['errors'])
    if results['buffer'] is None:
        update_download_element_from_parameters(element, {'status': 'error'})
        return
    buffer = results['buffer']
    md5 = get_buffer_checksum(buffer)
    post = get_post_by_md5(md5)
    if post is not None:
        update_illust_url_from_parameters(illust_url, {'post_id': post.id})
        update_download_element_from_parameters(element, {'status': 'duplicate', 'md5': md5})
        if post.type_name != 'user':
            update_post_from_parameters(post, {'type': 'user'})
        return
    if illust_url.type == 'image':
        results = create_image_post(buffer, illust_url, 'user')
    else:
        results = create_video_post(buffer, illust_url, 'user')
    create_and_extend_errors(element, results['errors'])
    if results['post'] is None:
        update_download_element_from_parameters(element, {'status': 'error'})
    else:
        update_download_element_from_parameters(element, {'status': 'complete', 'md5': md5})


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

def _create_download_illust(download):
    # Request URL should have already been validated, so no null test needed
    source = get_post_source(download.request_url)
    site_illust_id = source.get_illust_id(download.request_url)
    error = source.source_prework(site_illust_id)
    if error is not None:
        append_error(download, error)
    requery_time = days_ago(1)
    illust = Illust.query.enum_join(Illust.site_enum)\
                         .filter(Illust.site_filter('id', '__eq__', source.SITE.id),
                                 Illust.site_illust_id == site_illust_id)\
                         .one_or_none()
    if illust is None:
        illust = create_illust_from_source(site_illust_id, source)
        if illust is None:
            update_download_from_parameters(download, {'status': 'error'})
            create_and_append_error(download, 'download_rec.process_network_download',
                                    "Unable to create illust: %s" % (source.ILLUST_SHORTLINK % site_illust_id))
            return
    elif illust.updated < requery_time:
        update_illust_from_source(illust)
    # The artist will have already been created in the create illust step if it didn't exist
    if illust.artist.updated < requery_time:
        update_artist_from_source(illust.artist)
    return illust
