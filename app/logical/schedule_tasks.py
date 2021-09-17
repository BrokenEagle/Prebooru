# APP\LOGICAL\SCHEDULED_TASKS.PY

# ## PYTHON IMPORTS
import os
import time

# ## LOCAL IMPORTS
from .. import SESSION, SCHEDULER
from .utility import MinutesAgo, GetCurrentTime, SecondsFromNowLocal
from .check_booru_posts import CheckAllPostsForDanbooruID
from .check_booru_artists import CheckAllArtistsForBoorus
from ..models import Upload
from ..cache import ApiData, MediaFile
from ..database.upload_db import SetUploadStatus
from ..database.error_db import CreateAndAppendError

# ## GLOBAL VARIABLES


# ## FUNCTIONS

#@SCHEDULER.task("interval", id="check_timer", seconds=10, coalesce=True, misfire_grace_time=30, jitter=1)
#def check_timer():
#    print("Blah:", os.getpid())


#@SCHEDULER.task("interval", id="check_timer2", seconds=20, coalesce=True, misfire_grace_time=30, jitter=5)
#def check_timer2():
#    print("Blah2:", os.getpid())


@SCHEDULER.task("interval", id="expunge_cache_records", hours=1, jitter=300, next_run_time=SecondsFromNowLocal(5))
def expunge_cache_records_task():
    print("\n==========Expunge Cache Records==========")
    print("PID:", os.getpid())
    api_delete_count = ApiData.query.filter(ApiData.expires < GetCurrentTime()).count()
    print("API data records to delete:", api_delete_count)
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
                time.sleep(0.2)  # Time to let the OS remove the file to prevent OS errors
            SESSION.delete(media)
        SESSION.commit()
    print("=========================================\n")


@SCHEDULER.task("interval", id="expire_uploads", minutes=1, jitter=5)
def expire_uploads_task():
    print("\n==========Expire Uploads==========")
    print("PID:", os.getpid())
    expired_uploads = Upload.query.filter(Upload.created < MinutesAgo(5)).filter_by(status="processing").all()
    print("Uploads to expire:", len(expired_uploads))
    for upload in expired_uploads:
        SetUploadStatus(upload, 'complete')
        CreateAndAppendError('logical.scheduled_tasks.expire_uploads', "Upload has expired.", upload)
    print("==================================\n")


@SCHEDULER.task('interval', id="check_all_artists_for_boorus", days=1, jitter=3600)
def check_all_artists_for_boorus_task():
    print("\n==========Check All Artists==========")
    print("PID:", os.getpid())
    CheckAllArtistsForBoorus()
    print("=====================================\n")


@SCHEDULER.task('interval', id="check_all_posts_for_danbooru_id", days=1, jitter=3600)
def check_all_posts_for_danbooru_id_task():
    print("\n==========Check All Posts==========")
    print("PID:", os.getpid())
    CheckAllPostsForDanbooruID()
    print("===================================\n")
