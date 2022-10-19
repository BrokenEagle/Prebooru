# APP/CONTROLLERS/TASKS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, render_template, request, flash, redirect

# ## PACKAGE IMPORTS
from utility.data import eval_bool_string

# ## LOCAL IMPORTS
from .. import SCHEDULER
from ..logical.tasks.initialize import reschedule_task
from ..logical.database.jobs_db import get_all_job_enabled, get_all_job_locks, get_all_job_info,\
    update_job_enabled_status, update_job_manual_status


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
        SCHEDULER.add_job("%s-task" % name, _run_program, args=(TASK_MAP[name], name))
        reschedule_task(name, False)
    else:
        flash("Invalid task name.", 'error')
    return redirect(request.referrer)


# #### Private

def _initialize():
    global TASK_MAP
    #  Schedule is only importable after the app has been fully initialized, so wait until the first app request
    from ..logical.tasks import schedule
    tasknames = [k for k in dir(schedule) if k.endswith('_task') and not k.startswith('_')]
    TASK_MAP = dict((k[:-5], getattr(schedule, k)) for k in tasknames)


def _run_program(func, name):
    update_job_manual_status(name, True)
    try:
        func()
    finally:
        update_job_manual_status(name, False)


# ## INITIALIZE

bp.before_app_first_request(_initialize)
