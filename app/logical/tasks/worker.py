# APP/LOGICAL/TASKS/WORKER.PY

# ## PYTHON IMPORTS
import itertools
import threading

# ## PACKAGE IMPORTS
from utility.time import get_current_time, minutes_ago
from utility.print import buffered_print

# ## LOCAL IMPORTS
from ..utility import unique_objects
from ..similarity.generate_data import generate_post_similarity
from ..similarity.populate_pools import populate_similarity_pools
from ...models import Upload, Illust, SubscriptionPool
from ..check.posts import check_posts_for_danbooru_id
from ..check.booru_artists import check_artists_for_boorus
from ..check.subscriptions import download_subscription_illusts, download_subscription_elements
from ..records.artist_rec import update_artist_from_source
from ..records.illust_rec import create_illust_from_source, update_illust_from_source
from ..database.base_db import safe_db_execute
from ..database.post_db import get_posts_by_id
from ..database.upload_db import set_upload_status, has_duplicate_posts
from ..database.subscription_pool_db import update_subscription_pool_status, update_subscription_pool_active,\
    check_processing_subscriptions
from ..database.error_db import create_and_append_error, append_error
from ..database.jobs_db import get_job_status_data, update_job_status, update_job_lock_status
from ..sources.base import get_post_source, get_source_by_id
from ..downloader.network import convert_network_upload
from ..downloader.file import convert_file_upload


# ## FUNCTIONS

# #### Helper functions

def check_requery(instance):
    return instance.requery is None or instance.requery < get_current_time()


# #### Primary task functions

def process_upload(upload_id):
    printer = buffered_print("Process Upload")
    upload = None

    def try_func(scope_vars):
        nonlocal upload
        upload = Upload.find(upload_id)
        printer("Upload:", upload.id)
        set_upload_status(upload, 'processing')
        if upload.type == 'post':
            process_network_upload(upload)
        elif upload.type == 'file':
            process_file_upload(upload)

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
        if upload.status in ['complete', 'duplicate'] and len(upload.posts) > 0:
            printer("Starting secondary threads.")
            post_ids = [post.id for post in upload.posts]
            threading.Thread(target=process_similarity, args=(post_ids,)).start()
            threading.Thread(target=check_for_matching_danbooru_posts, args=(post_ids,)).start()
            threading.Thread(target=check_for_new_artist_boorus, args=(post_ids,)).start()

    safe_db_execute('process_upload', 'tasks.worker', try_func=try_func, msg_func=msg_func, error_func=error_func,
                    finally_func=finally_func, printer=printer)
    printer.print()


def process_subscription(subscription_id, job_id):
    printer = buffered_print("Process Subscription")
    subscription = None
    start_illusts = 0
    start_posts = 0
    start_elements = 0
    starting_post_ids = []

    def try_func(scope_vars):
        nonlocal subscription, start_illusts, start_posts, start_elements, starting_post_ids
        subscription = SubscriptionPool.find(subscription_id)
        start_illusts = subscription.artist.illust_count
        start_posts = subscription.artist.post_count
        start_elements = subscription.element_count
        starting_post_ids = [post.id for post in subscription.posts]
        update_job_lock_status('process_subscription', True)
        download_subscription_illusts(subscription, job_id)
        download_subscription_elements(subscription, job_id)
        job_status = get_job_status_data(job_id)
        job_status['stage'] = 'done'
        job_status['range'] = None
        update_job_status(job_id, job_status)

    def msg_func(scope_vars, e):
        return f"Unhandled exception occurred on subscripton pool #{subscription_id}: {repr(e)}"

    def error_func(scope_vars, e):
        nonlocal subscription
        subscription = subscription or SubscriptionPool.find(subscription_id)
        update_subscription_pool_status(subscription, 'error')
        update_subscription_pool_active(subscription, False)

    def finally_func(scope_vars, error, data):
        nonlocal subscription
        subscription = subscription or SubscriptionPool.find(subscription_id)
        if error is None and subscription.status != 'error':
            update_subscription_pool_status(subscription, 'idle')
        new_post_ids = [post.id for post in subscription.posts if post.id not in starting_post_ids]
        if len(new_post_ids):
            printer("Starting secondary threads.")
            threading.Thread(target=check_for_matching_danbooru_posts, args=(new_post_ids,)).start()
        threading.Timer(15, _query_unlock_subscription_job).start()  # Check later to give the DB time to catch up

    safe_db_execute('process_subscription', 'tasks.worker', try_func=try_func, msg_func=msg_func, printer=printer,
                    error_func=error_func, finally_func=finally_func)
    printer("Added illusts:", subscription.artist.illust_count - start_illusts)
    printer("Added posts:", subscription.artist.post_count - start_posts)
    printer("Added elements:", subscription.element_count - start_elements)
    printer.print()


# #### Secondary task functions

def process_similarity(post_ids):
    printer = buffered_print("Process Similarity")
    posts = get_posts_by_id(post_ids)
    for post in posts:
        generate_post_similarity(post, printer=printer)
        populate_similarity_pools(post, printer=printer)
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
            msg = "Unable to create illust: %s" % (source.ILLUST_SHORTLINK % site_illust_id)
            create_and_append_error('logical.worker_tasks.process_network_upload', msg, upload)
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


# #### Private functions

def _query_unlock_subscription_job():
    if not check_processing_subscriptions():
        update_job_lock_status('process_subscription', False)
