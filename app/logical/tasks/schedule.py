# APP\LOGICAL\TASKS\SCHEDULE.PY

# ## PYTHON IMPORTS
import os
import time

# ## LOCAL IMPORTS
from ... import DB, SESSION, SCHEDULER
from ..utility import get_current_time, seconds_from_now_local, buffered_print
from ..check.boorus import check_all_boorus
from ..check.posts import check_all_posts_for_danbooru_id
from ..check.booru_artists import check_all_artists_for_boorus
from ...models import Upload, ApiData, MediaFile
from ...database.upload_db import set_upload_status
from ...database.error_db import create_and_append_error

# ## GLOBAL VARIABLES


# ## FUNCTIONS

@SCHEDULER.task("interval", id="expunge_cache_records", hours=1, jitter=300, next_run_time=seconds_from_now_local(5))
def expunge_cache_records_task():
    printer = buffered_print("Expunge Cache Records")
    printer("PID:", os.getpid())
    api_delete_count = ApiData.query.filter(ApiData.expires < get_current_time()).count()
    printer("API data records to delete:", api_delete_count)
    if api_delete_count > 0:
        ApiData.query.filter(ApiData.expires < get_current_time()).delete()
        SESSION.commit()
    media_delete_count = MediaFile.query.filter(MediaFile.expires < get_current_time()).count()
    printer("Media files to delete:", media_delete_count)
    if media_delete_count > 0:
        media_records = MediaFile.query.filter(MediaFile.expires < get_current_time()).all()
        for media in media_records:
            if os.path.exists(media.file_path):
                os.remove(media.file_path)
                time.sleep(0.2)  # Time to let the OS remove the file to prevent OS errors
            SESSION.delete(media)
        SESSION.commit()
    printer.print()


@SCHEDULER.task('interval', id="check_all_boorus", days=1, jitter=3600)
def check_all_boorus_task():
    printer = buffered_print("Check All Boorus")
    printer("PID:", os.getpid())
    check_all_boorus(printer=printer)
    printer.print()


@SCHEDULER.task('interval', id="check_all_artists_for_boorus", days=1, jitter=3600)
def check_all_artists_for_boorus_task():
    printer = buffered_print("Check All Artists")
    printer("PID:", os.getpid())
    check_all_artists_for_boorus()
    printer.print()


@SCHEDULER.task('interval', id="check_all_posts_for_danbooru_id", days=1, jitter=3600)
def check_all_posts_for_danbooru_id_task():
    printer = buffered_print("Check All Posts")
    printer("PID:", os.getpid())
    check_all_posts_for_danbooru_id()
    printer.print()


@SCHEDULER.task('interval', id="vaccum_database", days=1, jitter=3600)
def vaccum_database():
    engine = DB.get_engine(bind=None).engine
    connection = engine.connect()
    connection.execute("VACUUM")
    connection.close()
