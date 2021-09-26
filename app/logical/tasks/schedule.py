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
from ..records.media_file_rec import batch_delete_media
from ...models import Upload, ApiData, MediaFile
from ...database.api_data_db import expired_api_data_count, delete_expired_api_data
from ...database.upload_db import set_upload_status
from ...database.media_file_db import get_expired_media_files, batch_delete_media_files
from ...database.error_db import create_and_append_error

# ## GLOBAL VARIABLES


# ## FUNCTIONS

@SCHEDULER.task("interval", id="expunge_cache_records", hours=1, jitter=300, next_run_time=seconds_from_now_local(5))
def expunge_cache_records_task():
    printer = buffered_print("Expunge Cache Records")
    printer("PID:", os.getpid())
    api_delete_count = expired_api_data_count()
    printer("API data records to delete:", api_delete_count)
    if api_delete_count > 0:
        delete_expired_api_data()
    expired_media_records = get_expired_media_files()
    printer("Media files to delete:", len(expired_media_records))
    if len(expired_media_records) > 0:
        batch_delete_media(expired_media_records)
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
