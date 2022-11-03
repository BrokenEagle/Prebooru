# APP/LOGICAL/RECORDS/UPLOAD_REC.PY

# ## PYTHON IMPORTS
import itertools

# ## PACKAGE IMPORTS
from utility.time import minutes_ago, days_ago
from utility.data import add_dict_entry
from utility.uprint import buffered_print, print_warning

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Upload, Illust
from ..utility import unique_objects, SessionThread
from ..sources.base import get_post_source
from ..records.artist_rec import update_artist_from_source, check_artists_for_boorus
from ..records.illust_rec import create_illust_from_source, update_illust_from_source
from ..records.post_rec import check_posts_for_danbooru_id
from ..records.image_hash_rec import generate_post_image_hashes
from ..records.similarity_match_rec import populate_similarity_pools
from ..database.base_db import safe_db_execute
from ..database.illust_db import get_site_illust, get_site_illusts
from ..database.upload_db import set_upload_status
from ..database.upload_element_db import create_upload_element_from_parameters
from ..database.post_db import get_posts_by_id
from ..database.error_db import create_and_append_error, append_error
from ..media import convert_mp4_to_webp, convert_mp4_to_webm
from ..downloader.network import convert_network_upload
from ..downloader.file import convert_file_upload


# ## FUNCTIONS

# #### Upload functions

def process_upload(upload_id):
    printer = buffered_print("Process Upload")
    upload = None

    def try_func(scope_vars):
        nonlocal upload
        upload = Upload.find(upload_id)
        printer("Upload:", upload.id)
        set_upload_status(upload, 'processing')
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
        set_upload_status(upload, 'error')

    def finally_func(scope_vars, error, data):
        nonlocal upload
        upload = upload or Upload.find(upload_id)
        printer("Upload:", upload.status)
        printer("Posts:", len(upload.posts))
        if upload.status.name in ['complete', 'duplicate'] and len(upload.posts) > 0:
            printer("Starting secondary threads.")
            post_ids = [post.id for post in upload.posts]
            SessionThread(target=process_image_matches, args=(post_ids,)).start()
            SessionThread(target=check_for_matching_danbooru_posts, args=(post_ids,)).start()
            SessionThread(target=check_for_new_artist_boorus, args=(post_ids,)).start()
            video_post_ids = [post.id for post in upload.posts if post.is_video]
            if len(video_post_ids):
                SessionThread(target=process_videos, args=(video_post_ids,)).start()

    safe_db_execute('process_upload', 'records.upload_rec',
                    try_func=try_func, msg_func=msg_func, printer=printer,
                    error_func=error_func, finally_func=finally_func)
    printer.print()
    SESSION.remove()


# #### Element functions

def populate_upload_elements(upload, illust=None):
    if illust is None:
        source = get_post_source(upload.request_url)
        site_illust_id = source.get_illust_id(upload.request_url)
        site_id = source.SITE_ID
        illust = get_site_illust(site_illust_id, site_id)
        if illust is None:
            return
    else:
        source = illust.site_id.source
    all_upload_urls = [source.normalize_image_url(upload_url.url) for upload_url in upload.image_urls]
    upload_elements = list(upload.elements)
    for illust_url in illust.urls:
        if (len(all_upload_urls) > 0) and (illust_url.url not in all_upload_urls):
            continue
        element = next((element for element in upload_elements if element.illust_url_id == illust_url.id), None)
        if element is None:
            element = create_upload_element_from_parameters({'upload_id': upload.id, 'illust_url_id': illust_url.id},
                                                            commit=False)
            upload_elements.append(element)
    return upload_elements


def populate_all_upload_elements(uploads):
    illust_lookup = {}
    illust_index = {}
    upload_elements = {}
    for upload in uploads:
        source = upload._source
        if upload.request_url is not None:
            site_illust_id = source.get_illust_id(upload.request_url)
        elif upload.illust_url_id is not None:
            site_illust_id = upload.illust_url.illust.site_illust_id
        else:
            print_warning(f"Unable to find an illust for {upload.shortlink}")
            continue
        site_id = source.SITE_ID
        add_dict_entry(illust_lookup, site_id, site_illust_id)
        illust_index[upload.id] = {'site_id': site_id, 'site_illust_id': site_illust_id}
    illusts = []
    for key in illust_lookup:
        illusts += get_site_illusts(key, illust_lookup[key], load_urls=True)
    for upload in uploads:
        illust_params = illust_index[upload.id]
        illust = next((illust for illust in illusts
                       if illust.site_id.value == illust_params['site_id']
                       and illust.site_illust_id == illust_params['site_illust_id']), None)
        if illust is None:
            continue
        upload_elements[upload.id] = populate_upload_elements(upload, illust=illust)
    return upload_elements


# #### Auxiliary functions

def process_network_upload(upload):
    # Request URL should have already been validated, so no null test needed
    source = get_post_source(upload.request_url)
    site_illust_id = source.get_illust_id(upload.request_url)
    site_id = source.SITE_ID
    error = source.source_prework(site_illust_id)
    if error is not None:
        append_error(upload, error)
    requery_time = days_ago(1)
    illust = Illust.query.filter_by(site_id=site_id, site_illust_id=site_illust_id).one_or_none()
    if illust is None:
        illust = create_illust_from_source(site_illust_id, source)
        if illust is None:
            set_upload_status(upload, 'error')
            msg = "Unable to create illust: %s" % (source.ILLUST_SHORTLINK % site_illust_id)
            create_and_append_error('records.upload_rec.process_network_upload', msg, upload)
            return
    elif illust.updated < requery_time:
        update_illust_from_source(illust)
    # The artist will have already been created in the create illust step if it didn't exist
    if illust.artist.updated < requery_time:
        update_artist_from_source(illust.artist)
    all_upload_urls = [source.normalize_image_url(upload_url.url) for upload_url in upload.image_urls]
    upload_elements = upload.elements
    for illust_url in illust.urls:
        if (len(all_upload_urls) > 0) and (illust_url.url not in all_upload_urls):
            continue
        element = next((element for element in upload_elements if element.illust_url_id == illust_url.id), None)
        if element is None:
            element = create_upload_element_from_parameters({'upload_id': upload.id, 'illust_url_id': illust_url.id})
        if convert_network_upload(element):
            upload.successes += 1
        else:
            upload.failures += 1
    set_upload_status(upload, 'complete')


def process_file_upload(upload):
    illust = upload.illust_url.illust
    requery_time = days_ago(1)
    if illust.updated < requery_time:
        update_illust_from_source(illust)
    if illust.artist.updated < requery_time:
        update_artist_from_source(illust.artist)
    if convert_file_upload(upload):
        set_upload_status(upload, 'complete')
    else:
        set_upload_status(upload, 'error')


# #### Secondary task functions

def process_image_matches(post_ids):
    printer = buffered_print("Process Image Matches")
    posts = get_posts_by_id(post_ids)
    for post in posts:
        generate_post_image_hashes(post, printer=printer)
        populate_similarity_pools(post, printer=printer)
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
