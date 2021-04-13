# WORKER.PY

# ## PYTHON IMPORTS
import os
import time
from flask import jsonify
from sqlalchemy import not_
from sqlalchemy.orm import Session
import atexit
import random
import threading
import itertools
from apscheduler.schedulers.background import BackgroundScheduler
from argparse import ArgumentParser

# ## LOCAL IMPORTS
from app import database
from app import DB, SESSION, PREBOORU_APP
from app.cache import ApiData, MediaFile
from app.models import Upload, Illust, Artist, Booru
from app.database.artist_db import UpdateArtistFromSource
from app.database.booru_db import CreateBooruFromParameters, BooruAppendArtist
from app.database.illust_db import CreateIllustFromSource, UpdateIllustFromSource
from app.database.upload_db import IsDuplicate, SetUploadStatus
from app.database.error_db import AppendError, CreateAndAppendError
from app.sources.base_source import GetPostSource, GetSourceById
from app.sources.local_source import SimilarityCheckPosts
from app.sources.danbooru_source import GetArtistsByMultipleUrls
from app.logical.utility import MinutesAgo, GetCurrentTime, SecondsFromNowLocal
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
BOORU_SEM = threading.Semaphore()

BOORU_ARTISTS_DATA = None
BOORU_ARTISTS_FILE = WORKING_DIRECTORY + DATA_FILEPATH + 'booru_artists_file.json'

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


def SaveLastCheckArtistId(max_artist_id):
    BOORU_ARTISTS_DATA['last_checked_artist_id'] = max_artist_id
    PutGetJSON(BOORU_ARTISTS_FILE, 'w', BOORU_ARTISTS_DATA)


def LoadBooruArtistData():
    global BOORU_ARTISTS_DATA
    if BOORU_ARTISTS_DATA is None:
        BOORU_ARTISTS_DATA = PutGetJSON(BOORU_ARTISTS_FILE, 'r')
        BOORU_ARTISTS_DATA = BOORU_ARTISTS_DATA if type(BOORU_ARTISTS_DATA) is dict else {}
        BOORU_ARTISTS_DATA['last_checked_artist_id'] = BOORU_ARTISTS_DATA['last_checked_artist_id'] if ('last_checked_artist_id' in BOORU_ARTISTS_DATA) and (type(BOORU_ARTISTS_DATA['last_checked_artist_id']) is int) else 0


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
    post_ids = []
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
                post_ids.extend(upload.post_ids)
            else:
                print("No pending uploads.")
                break
            time.sleep(5)
    finally:
        if len(post_ids) > 0:
            SCHED.add_job(ContactSimilarityServer)
            SCHED.add_job(CheckForNewArtistBoorus)
        UPLOAD_SEM.release()
        print("\n<upload semaphore release>\n")


def ContactSimilarityServer():
    results = SimilarityCheckPosts()
    if results['error']:
        print("Similarity error:", results['message'])


def CheckForNewArtistBoorus():
    BOORU_SEM.acquire()
    print("<\nbooru semaphore acquire>\n")
    try:
        LoadBooruArtistData()
        page = Artist.query.filter(Artist.id > BOORU_ARTISTS_DATA['last_checked_artist_id'], not_(Artist.boorus.any())).paginate(per_page=100)
        max_artist_id = 0
        while True:
            if len(page.items) == 0:
                break
            query_urls = [artist.booru_search_url for artist in page.items]
            results = GetArtistsByMultipleUrls(query_urls)
            if results['error']:
                print("Danbooru error:", results)
                break
            booru_artist_ids = set(artist['id'] for artist in itertools.chain(*[results['data'][url] for url in results['data']]))
            boorus = Booru.query.filter(Booru.danbooru_id.in_(booru_artist_ids)).all()
            for url in results['data']:
                AddDanbooruArtists(url, results['data'][url], boorus, page.items)
            max_artist_id = max(max_artist_id, *[artist.id for artist in page.items])
            SaveLastCheckArtistId(max_artist_id)
            if not page.has_next:
                break
            page = page.next()
    finally:
        BOORU_SEM.release()
        print("\n<booru semaphore release>\n")


def ExpireUploads():
    time.sleep(random.random() * 5)
    print("\nExpireUploads")
    expired_uploads = Upload.query.filter(Upload.created < MinutesAgo(5)).filter_by(status="processing").all()
    if len(expired_uploads):
        print("Found %d uploads to expire!" % len(expired_uploads))
    for upload in expired_uploads:
        SetUploadStatus(upload, 'complete')
        database.local.CreateAndAppendError('worker.ExpireUploads', "Upload has expired.", upload)


def ExpungeCacheRecords():
    print("\nExpungeCacheRecords")
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
        SCHED.add_job(ExpungeCacheRecords, 'interval', hours=1, next_run_time=SecondsFromNowLocal(5))
        SCHED.add_job(CheckPendingUploads, 'interval', minutes=5, next_run_time=SecondsFromNowLocal(15))
        SCHED.add_job(CheckForNewArtistBoorus, 'interval', minutes=5)
        SCHED.add_job(ExpireUploads, 'interval', minutes=1)
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
