# APP/CONTROLLERS/TASKS_CONTROLLER.PY

# ## PYTHON IMPORTS
import threading

# ## EXTERNAL IMPORTS
from flask import Blueprint, render_template, request, flash, redirect

# ## PACKAGE IMPORTS
from utility.data import eval_bool_string

# ## LOCAL IMPORTS
from ..logical.tasks.initialize import reschedule_task
from ..logical.database.jobs_db import get_all_job_enabled, get_all_job_locks, get_all_job_info,\
    update_job_enabled_status


# ## GLOBAL VARIABLES

bp = Blueprint("task", __name__)

TASKS_MAP = None


# ## FUNCTIONS

# #### Route functions

@bp.route('/tasks', methods=['GET'])
def list_html():
    enabled = get_all_job_enabled()
    locks = get_all_job_locks()
    timevals = get_all_job_info()
    return render_template("tasks/list.html", tasks={'enabled': enabled, 'locks': locks, 'timevals': timevals})


@bp.route('/tasks/<name>', methods=['PUT'])
def update_html(name):
    if name in TASK_MAP:
        enable = request.values.get('enable', type=eval_bool_string)
        if enable is not None:
            flash(f"Updated value for '{name}': {enable}")
            update_job_enabled_status(name, enable)
        else:
            flash("Enable argument not set.", 'error')
    else:
        flash("Invalid task name.", 'error')
    return redirect(request.referrer)


@bp.route('/tasks/<name>/run', methods=['POST'])
def run_html(name):
    if name in TASK_MAP:
        flash("Running task '%s'." % name)
        threading.Thread(target=TASK_MAP[name]).start()
        reschedule_task(name, False)
    else:
        flash("Invalid task name.", 'error')
    return redirect(request.referrer)


# #### Private

def _initialize():
    global TASK_MAP
    print("tasks_controller._initialize")
    #  Schedule is only importable after the app has been fully initialized, so wait until the first app request
    from ..logical.tasks.schedule import check_all_boorus_task, check_all_artists_for_boorus_task,\
        check_all_posts_for_danbooru_id_task, expunge_cache_records_task, expunge_archive_records_task,\
        delete_orphan_images_task, vacuum_analyze_database_task, check_pending_subscriptions, check_pending_downloads,\
        process_expired_subscription_elements
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


# ## INITIALIZE

bp.before_app_first_request(_initialize)
