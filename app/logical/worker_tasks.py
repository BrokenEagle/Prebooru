# APP\LOGICAL\WORKER_TASKS.PY

# ## PYTHON IMPORTS
import itertools

# ## LOCAL IMPORTS
from .. import SESSION, SCHEDULER, THREADULER
from .utility import GetCurrentTime, MinutesAgo, UniqueObjects
from .logger import LogError
from ..models import Upload, Post, Illust
from .check_booru_posts import CheckPostsForDanbooruID
from .check_booru_artists import CheckArtistsForBoorus
from ..database.artist_db import UpdateArtistFromSource
from ..database.illust_db import CreateIllustFromSource, UpdateIllustFromSource
from ..database.upload_db import SetUploadStatus, IsDuplicate
from ..database.error_db import CreateAndAppendError, AppendError
from ..sources.base_source import GetPostSource, GetSourceById
from ..sources.local_source import SimilarityCheckPosts
from ..downloader.network_downloader import ConvertNetworkUpload
from ..downloader.file_downloader import ConvertFileUpload


# ## GLOBAL VARIABLES


# ## FUNCTIONS

# #### Helper functions

def check_requery(instance):
    return instance.requery is None or instance.requery < GetCurrentTime()


# #### Task functions

def process_upload(upload_id):
    print("\n==========Process Upload==========")
    upload = Upload.find(upload_id)
    print("Upload:", upload)
    SetUploadStatus(upload, 'processing')
    try:
        if upload.type == 'post':
            process_network_upload(upload)
        elif upload.type == 'file':
            process_file_upload(upload)
    except Exception as e:
        print("\a\aProcessUpload: Exception occured in worker!\n", e)
        print("Unlocking the database...")
        SESSION.rollback()
        LogError('worker.ProcessUpload', "Unhandled exception occurred on upload #%d: %s" % (upload.id, e))
        SetUploadStatus(upload, 'error')
    finally:
        print("Upload:", upload.status)
        print("Posts:", len(upload.posts))
        if upload.status in ['complete', 'duplicate'] and len(upload.posts) > 0:
            print("Adding secondary jobs.")
            THREADULER.add_job(contact_similarity_server, id="contact_similarity_server-%d" % upload.id)
            post_ids = [post.id for post in upload.posts]
            THREADULER.add_job(check_for_matching_danbooru_posts, id="check_for_matching_danbooru_posts-%d" % upload.id, args=(post_ids,))
            THREADULER.add_job(check_for_new_artist_boorus, args=(post_ids,), id="check_for_new_artist_boorus-%d" % upload.id)
    print("=================================\n")


def contact_similarity_server():
    print("\n==========Contact Similarity==========")
    results = SimilarityCheckPosts()
    print("Result:", "success" if not results['error'] else "failure")
    if results['error']:
        print("Similarity error:", results['message'])
    print("======================================\n")


def check_for_matching_danbooru_posts(post_ids):
    print("\n==========Check Danbooru Posts==========")
    print("Posts to check:", len(post_ids))
    posts = Post.query.filter(Post.id.in_(post_ids)).all()
    CheckPostsForDanbooruID(posts)
    print("========================================\n")


def check_for_new_artist_boorus(post_ids):
    print("\n==========Check Artist Boorus==========")
    posts = Post.query.filter(Post.id.in_(post_ids)).all()
    all_artists = UniqueObjects([*itertools.chain(*[post.artists for post in posts])])
    check_artists = [artist for artist in all_artists if artist.created > MinutesAgo(1)]
    print("Artists to check:", len(check_artists))
    if len(check_artists):
        CheckArtistsForBoorus(check_artists)
    print("=======================================\n")


# #### Auxiliary functions

def process_network_upload(upload):
    # Request URL should have already been validated, so no null test needed
    source = GetPostSource(upload.request_url)
    site_illust_id = source.GetIllustId(upload.request_url)
    site_id = source.SITE_ID
    error = source.Prework(site_illust_id)
    if error is not None:
        AppendError(upload, error)
    illust = Illust.query.filter_by(site_id=site_id, site_illust_id=site_illust_id).first()
    if illust is None:
        illust = CreateIllustFromSource(site_illust_id, source)
        if illust is None:
            SetUploadStatus(upload, 'error')
            CreateAndAppendError('logical.worker_tasks.process_network_upload', "Unable to create illust: %s" % (source.ILLUST_SHORTLINK % site_illust_id), upload)
            return
    elif check_requery(illust):
        UpdateIllustFromSource(illust, source)
    # The artist will have already been created in the create illust step if it didn't exist
    if check_requery(illust.artist):
        UpdateArtistFromSource(illust.artist, source)
    if ConvertNetworkUpload(illust, upload, source):
        SetUploadStatus(upload, 'complete')
    elif IsDuplicate(upload):
        SetUploadStatus(upload, 'duplicate')
    else:
        SetUploadStatus(upload, 'error')


def process_file_upload(upload):
    illust = upload.illust_url.illust
    source = GetSourceById(illust.site_id)
    if check_requery(illust):
        UpdateIllustFromSource(illust, source)
    if check_requery(illust.artist):
        UpdateArtistFromSource(illust.artist, source)
    if ConvertFileUpload(upload, source):
        SetUploadStatus(upload, 'complete')
    else:
        SetUploadStatus(upload, 'error')
