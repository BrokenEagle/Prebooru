# WORKER.PY

# ## PYTHON IMPORTS
import os
import time
from flask import jsonify
from sqlalchemy.orm import Session
import atexit
import threading
import itertools
from apscheduler.schedulers.background import BackgroundScheduler
from argparse import ArgumentParser

# ## LOCAL IMPORTS
from app import database
from app import DB, SESSION, PREBOORU_APP
from app.cache import ApiData, MediaFile
from app.models import Upload, Illust, Post
from app.database.artist_db import UpdateArtistFromSource
from app.database.booru_db import CreateBooruFromParameters, BooruAppendArtist
from app.database.illust_db import CreateIllustFromSource, UpdateIllustFromSource
from app.database.upload_db import IsDuplicate, SetUploadStatus
from app.database.error_db import AppendError, CreateAndAppendError
from app.sources.base_source import GetPostSource, GetSourceById
from app.sources.local_source import SimilarityCheckPosts
from app.logical.check_booru_posts import CheckAllPostsForDanbooruID, CheckPostsForDanbooruID
from app.logical.check_booru_artists import CheckAllArtistsForBoorus, CheckArtistsForBoorus
from app.logical.utility import MinutesAgo, GetCurrentTime, SecondsFromNowLocal, UniqueObjects
from app.logical.file import LoadDefault, PutGetJSON
from app.logical.logger import LogError
from app.downloader.network_downloader import ConvertNetworkUpload
from app.downloader.file_downloader import ConvertFileUpload
from app.config import WORKING_DIRECTORY, DATA_FILEPATH, WORKER_PORT, DEBUG_MODE, VERSION


# ## GLOBAL VARIABLES

SERVER_PID_FILE = WORKING_DIRECTORY + DATA_FILEPATH + 'worker-server-pid.json'
SERVER_PID = next(iter(LoadDefault(SERVER_PID_FILE, [])), None)

SCHED = None
UPLOAD_SEM = threading.Semaphore()

READ_ENGINE = DB.engine.execution_options(isolation_level="READ UNCOMMITTED")


# ### FUNCTIONS

# #### Route functions

@PREBOORU_APP.route('/check_uploads')
def check_uploads():
    SCHED.add_job(CheckPendingUploads)
    return jsonify(UPLOAD_SEM._value > 0)


# #### Helper functions

def CheckRequery(instance):
    return instance.requery is None or instance.requery < GetCurrentTime()


def GetPendingUploadIDs():
    # Doing this because there were issues with subsequent iterations of the
    # while loop in ProcessUploads not registering newly created uploads.
    with Session(bind=READ_ENGINE) as session:
        return [upload.id for upload in session.query(Upload).filter_by(status="pending").all()]


def GetUploadWait(upload_id):
    for i in range(3):
        upload = Upload.find(upload_id)
        if upload is not None:
            return upload
        time.sleep(0.5)


# #### Upload functions

def ProcessUploadWrap(upload):
    try:
        ProcessUpload(upload)
        return True
    except Exception as e:
        print("\a\aProcessUpload: Exception occured in worker!\n", e)
        print("Unlocking the database...")
        SESSION.rollback()
        LogError('worker.ProcessUpload', "Unhandled exception occurred on upload #%d: %s" % (upload.id, e))
        SetUploadStatus(upload, 'error')
        return False


def ProcessUpload(upload):
    SetUploadStatus(upload, 'processing')
    if upload.type == 'post':
        ProcessNetworkUpload(upload)
    elif upload.type == 'file':
        ProcessFileUpload(upload)


def ProcessNetworkUpload(upload):
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
            CreateAndAppendError('worker.ProcessNetworkUpload', "Unable to create illust: %s" % (source.ILLUST_SHORTLINK % site_illust_id), upload)
            return
    elif CheckRequery(illust):
        UpdateIllustFromSource(illust, source)
    # The artist will have already been created in the create illust step if it didn't exist
    if CheckRequery(illust.artist):
        UpdateArtistFromSource(illust.artist, source)
    if ConvertNetworkUpload(illust, upload, source):
        SetUploadStatus(upload, 'complete')
    elif IsDuplicate(upload):
        SetUploadStatus(upload, 'duplicate')
    else:
        SetUploadStatus(upload, 'error')


def ProcessFileUpload(upload):
    illust = upload.illust_url.illust
    source = GetSourceById(illust.site_id)
    if CheckRequery(illust):
        UpdateIllustFromSource(illust, source)
    if CheckRequery(illust.artist):
        UpdateArtistFromSource(illust.artist, source)
    if ConvertFileUpload(upload, source):
        SetUploadStatus(upload, 'complete')
    else:
        SetUploadStatus(upload, 'error')


# #### Booru functions

def AddDanbooruArtists(url, danbooru_artists, db_boorus, db_artists):
    artist = next(filter(lambda x: x.booru_search_url == url, db_artists))
    for danbooru_artist in danbooru_artists:
        booru = next(filter(lambda x: x.danbooru_id == danbooru_artist['id'], db_boorus), None)
        if booru is None:
            booru = CreateBooruFromParameters({'danbooru_id': danbooru_artist['id'], 'current_name': danbooru_artist['name']})
        BooruAppendArtist(booru, artist)


# #### Scheduled functions

def CheckPendingUploads():
    UPLOAD_SEM.acquire()
    print("\n<upload semaphore acquire>\n")
    posts = []
    try:
        while True:
            print("Current upload count:", SESSION.query(Upload).count())
            upload_ids = GetPendingUploadIDs()
            for upload_id in upload_ids:
                # Must retrieve the upload with Flask session object for updating/appending to work
                upload = GetUploadWait(upload_id)
                if upload is None:
                    raise Exception("\aUnable to find upload with upload id: %d" % upload_id)
                if not ProcessUploadWrap(upload):
                    return
                posts.extend(upload.posts)
            else:
                print("No pending uploads.")
                break
            time.sleep(5)
    finally:
        if len(posts) > 0:
            SCHED.add_job(ContactSimilarityServer)
            post_ids = [post.id for post in posts]
            SCHED.add_job(CheckForMatchingDanbooruPosts, args=(post_ids,))
            SCHED.add_job(CheckForNewArtistBoorus, args=(post_ids,))
        UPLOAD_SEM.release()
        print("\n<upload semaphore release>\n")


def ContactSimilarityServer():
    results = SimilarityCheckPosts()
    if results['error']:
        print("Similarity error:", results['message'])


def CheckForMatchingDanbooruPosts(post_ids):
    posts = Post.query.filter(Post.id.in_(post_ids)).all()
    CheckPostsForDanbooruID(posts)


def CheckForNewArtistBoorus(post_ids):
    posts = Post.query.filter(Post.id.in_(post_ids)).all()
    all_artists = UniqueObjects([*itertools.chain(*[post.artists for post in posts])])
    check_artists = [artist for artist in all_artists if artist.created > MinutesAgo(1)]
    if len(check_artists):
        print("Artists to check:", len(check_artists))
        CheckArtistsForBoorus(check_artists)


def ExpireUploads():
    expired_uploads = Upload.query.filter(Upload.created < MinutesAgo(5)).filter_by(status="processing").all()
    print("Uploads to expire:", len(expired_uploads))
    for upload in expired_uploads:
        SetUploadStatus(upload, 'complete')
        database.local.CreateAndAppendError('worker.ExpireUploads', "Upload has expired.", upload)


def ExpungeCacheRecords():
    api_delete_count = ApiData.query.filter(ApiData.expires < GetCurrentTime()).count()
    print("Records to delete:", api_delete_count)
    if api_delete_count > 0:
        ApiData.query.filter(ApiData.expires < GetCurrentTime()).delete()
        SESSION.commit()
    media_delete_count = MediaFile.query.filter(MediaFile.expires < GetCurrentTime()).count()
    print("Media files to delete:", media_delete_count)
    if media_delete_count > 0:
        media_records = MediaFile.query.filter(MediaFile.expires < GetCurrentTime()).all()
        for media in media_records:
            if os.path.exists(media.file_path):
                os.remove(media.file_path)
                time.sleep(0.2)
            SESSION.delete(media)
        SESSION.commit()


# #### Initialization

os.environ['FLASK_ENV'] = 'development' if DEBUG_MODE else 'production'


@atexit.register
def Cleanup():
    if SERVER_PID is not None:
        PutGetJSON(SERVER_PID_FILE, 'w', [])
    if SCHED is not None and SCHED.running:
        SCHED.shutdown()


# #### Main function

def Main(args):
    global SERVER_PID, SCHED
    if SERVER_PID is not None:
        print("\nServer process already running: %d" % SERVER_PID)
        input()
        exit(-1)
    if args.logging:
        import logging
        logging.basicConfig()
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    if args.title:
        os.system('title Worker Server')
    if not DEBUG_MODE or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        print("\n========== Starting server - Worker-%s ==========" % VERSION)
        SERVER_PID = os.getpid()
        PutGetJSON(SERVER_PID_FILE, 'w', [SERVER_PID])
        SCHED = BackgroundScheduler(daemon=True)
        SCHED.add_job(ExpungeCacheRecords, 'interval', hours=1, next_run_time=SecondsFromNowLocal(5), jitter=300)
        SCHED.add_job(CheckPendingUploads, 'interval', minutes=5, next_run_time=SecondsFromNowLocal(15), jitter=60)
        SCHED.add_job(CheckAllArtistsForBoorus, 'interval', days=1, jitter=3600)
        SCHED.add_job(CheckAllPostsForDanbooruID, 'interval', days=1, jitter=3600)
        SCHED.add_job(ExpireUploads, 'interval', minutes=1, jitter=5)
        SCHED.start()
    PREBOORU_APP.name = 'worker'
    PREBOORU_APP.run(threaded=True, port=WORKER_PORT)


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Worker to process uploads.")
    parser.add_argument('--logging', required=False, default=False, action="store_true", help="Display the SQL commands.")
    parser.add_argument('--title', required=False, default=False, action="store_true", help="Adds server title to console window.")
    args = parser.parse_args()
    Main(args)
