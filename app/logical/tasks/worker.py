# APP\LOGICAL\TASKS\WORKER.PY

# ## PYTHON IMPORTS
import itertools
import threading

# ## LOCAL IMPORTS
from ... import SESSION
from ..utility import get_current_time, minutes_ago, unique_objects, buffered_print
from ..logger import log_error
from ..similarity.generate_data import generate_post_similarity
from ..similarity.populate_pools import populate_similarity_pools
from ...models import Upload, Post, Illust
from ..check.posts import check_posts_for_danbooru_id
from ..check.booru_artists import check_artists_for_boorus
from ...database.artist_db import update_artist_from_source
from ...database.illust_db import create_illust_from_source, update_illust_from_source
from ...database.upload_db import set_upload_status, has_duplicate_posts
from ...database.error_db import create_and_append_error, append_error
from ...sources.base_source import get_post_source, get_source_by_id
from ..downloader.network import convert_network_upload
from ..downloader.file import convert_file_upload


# ## GLOBAL VARIABLES


# ## FUNCTIONS

# #### Helper functions

def check_requery(instance):
    return instance.requery is None or instance.requery < get_current_time()


# #### Task functions

def process_upload(upload_id):
    printer = buffered_print("Process Upload")
    upload = Upload.find(upload_id)
    printer("Upload:", upload)
    set_upload_status(upload, 'processing')
    try:
        if upload.type == 'post':
            process_network_upload(upload)
        elif upload.type == 'file':
            process_file_upload(upload)
    except Exception as e:
        printer("\a\aProcessUpload: Exception occured in worker!\n", e)
        printer("Unlocking the database...")
        SESSION.rollback()
        log_error('worker.ProcessUpload', "Unhandled exception occurred on upload #%d: %s" % (upload.id, e))
        set_upload_status(upload, 'error')
    finally:
        printer("Upload:", upload.status)
        printer("Posts:", len(upload.posts))
        if upload.status in ['complete', 'duplicate'] and len(upload.posts) > 0:
            printer("Starting secondary threads.")
            post_ids = [post.id for post in upload.posts]
            threading.Thread(target=process_similarity, args=(post_ids,)).start()
            threading.Thread(target=check_for_matching_danbooru_posts, args=(post_ids,)).start()
            threading.Thread(target=check_for_new_artist_boorus, args=(post_ids,)).start()
    printer.print()


def process_similarity(post_ids):
    printer = buffered_print("Process Similarity")
    posts = Post.query.filter(Post.id.in_(post_ids)).all()
    for post in posts:
        generate_post_similarity(post, printer=printer)
        populate_similarity_pools(post, printer=printer)
    printer.print()


def check_for_matching_danbooru_posts(post_ids):
    printer = buffered_print("Check Danbooru Posts")
    printer("Posts to check:", len(post_ids))
    posts = Post.query.filter(Post.id.in_(post_ids)).all()
    check_posts_for_danbooru_id(posts)
    printer.print()


def check_for_new_artist_boorus(post_ids):
    printer = buffered_print("Check Artist Boorus")
    posts = Post.query.filter(Post.id.in_(post_ids)).all()
    all_artists = unique_objects([*itertools.chain(*[post.artists for post in posts])])
    check_artists = [artist for artist in all_artists if artist.created > minutes_ago(1)]
    printer("Artists to check:", len(check_artists))
    if len(check_artists):
        check_artists_for_boorus(check_artists)
    printer.print()


# #### Auxiliary functions

def process_network_upload(upload):
    # Request URL should have already been validated, so no null test needed
    source = get_post_source(upload.request_url)
    site_illust_id = source.get_illust_id(upload.request_url)
    site_id = source.SITE_ID
    error = source.source_prework(site_illust_id)
    if error is not None:
        append_error(upload, error)
    illust = Illust.query.filter_by(site_id=site_id, site_illust_id=site_illust_id).first()
    if illust is None:
        illust = create_illust_from_source(site_illust_id, source)
        if illust is None:
            set_upload_status(upload, 'error')
            create_and_append_error('logical.worker_tasks.process_network_upload', "Unable to create illust: %s" % (source.ILLUST_SHORTLINK % site_illust_id), upload)
            return
    elif check_requery(illust):
        update_illust_from_source(illust, source)
    # The artist will have already been created in the create illust step if it didn't exist
    if check_requery(illust.artist):
        update_artist_from_source(illust.artist, source)
    if convert_network_upload(illust, upload, source):
        set_upload_status(upload, 'complete')
    elif has_duplicate_posts(upload):
        set_upload_status(upload, 'duplicate')
    else:
        set_upload_status(upload, 'error')


def process_file_upload(upload):
    illust = upload.illust_url.illust
    source = get_source_by_id(illust.site_id)
    if check_requery(illust):
        update_illust_from_source(illust, source)
    if check_requery(illust.artist):
        update_artist_from_source(illust.artist, source)
    if convert_file_upload(upload, source):
        set_upload_status(upload, 'complete')
    else:
        set_upload_status(upload, 'error')
