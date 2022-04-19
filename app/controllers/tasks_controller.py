# APP/CONTROLLERS/TASKS_CONTROLLER.PY

# ## PYTHON IMPORTS
import os
import threading

# ## EXTERNAL IMPORTS
from flask import Blueprint, render_template, send_from_directory, request, flash, redirect

# ## LOCAL IMPORTS
from .. import PREBOORU_APP
from ..logical.tasks.initialize import reschedule_task


# ## GLOBAL VARIABLES

bp = Blueprint("task", __name__)

TASKS_MAP = None


# ## FUNCTIONS

@bp.route('/tasks', methods=['GET'])
def tasks_html():
    return render_template("tasks/tasks.html")


@bp.route('/tasks/<name>/run', methods=['POST'])
def run_task_html(name):
    if name in TASK_MAP:
        flash("Running task '%s'." % name)
        threading.Thread(target=TASK_MAP[name]).start()
        reschedule_task(name, JOB_CONFIG, JOB_LEEWAY, False)
    else:
        flash("Invalid task name.", 'error')
    return redirect(request.referrer)

# #### Private

def _initialize():
    global TASK_MAP, JOB_CONFIG, JOB_LEEWAY
    print("tasks_controller._initialize")
    # Schedule is only importable after the app has been fully initialized, so wait until the first app request
    from ..logical.tasks.schedule import JOB_CONFIG, JOB_LEEWAY, check_all_boorus_task, check_all_artists_for_boorus_task, check_all_posts_for_danbooru_id_task,\
        expunge_cache_records_task, expunge_archive_records_task, delete_orphan_images_task, vacuum_analyze_database_task, check_pending_subscriptions,\
        check_pending_downloads, process_expired_subscription_elements
    TASK_MAP = {
        'check_all_boorus': check_all_boorus_task,
        'check_all_artists_for_boorus': check_all_artists_for_boorus_task,
        'check_all_posts_for_danbooru_id': check_all_posts_for_danbooru_id_task,
        'check_pending_subscriptions': check_pending_subscriptions,
        'check_pending_downloads': check_pending_downloads,
        'process_expired_subscription_elements': process_expired_subscription_elements,
        'expunge_cache_records': expunge_cache_records_task,
        'expunge_archive_records': expunge_archive_records_task,
        'delete_orphan_images': delete_orphan_images_task,
        'vacuum_analyze_database': vacuum_analyze_database_task,
    }

bp.before_app_first_request(_initialize)
