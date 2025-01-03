# APP/CONTROLLERS/TASKS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, render_template, request, flash, redirect

# ## PACKAGE IMPORTS
from utility.data import eval_bool_string

# ## LOCAL IMPORTS
from .. import SCHEDULER, SESSION
from ..logical.tasks.reschedule import reschedule_task
from ..logical.database.jobs_db import get_all_job_items, get_all_job_info, update_job_by_id


# ## GLOBAL VARIABLES

bp = Blueprint("task", __name__)

TASKS_MAP = None


# ## FUNCTIONS

# #### Route functions

@bp.route('/tasks', methods=['GET'])
def list_html():
    enabled = {item.id: item.enabled for item in get_all_job_items('job_enable').values()}
    locks = {item.id: item.locked for item in get_all_job_items('job_lock').values()}
    timevals = get_all_job_info()
    return render_template("tasks/list.html", tasks={'enabled': enabled, 'locks': locks, 'timevals': timevals})


@bp.route('/tasks/<name>', methods=['PUT'])
def update_html(name):
    if name in TASK_MAP:
        enable = request.values.get('enable', type=eval_bool_string)
        if enable is not None:
            flash(f"Updated value for '{name}': {enable}")
            update_job_by_id('job_enable', name, {'enabled': enable})
            SESSION.commit()
        else:
            flash("Enable argument not set.", 'error')
    else:
        flash("Invalid task name.", 'error')
    return redirect(request.referrer)


@bp.route('/tasks/<name>/run', methods=['POST'])
def run_html(name):
    if name in TASK_MAP:
        flash("Running task '%s'." % name)
        manual = request.values.get('manual', type=eval_bool_string)
        SCHEDULER.add_job("%s-task" % name, _run_program, args=(TASK_MAP[name], name, manual))
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


def _run_program(func, name, manual):
    if manual:
        update_job_by_id('job_manual', name, {'manual': True})
        SESSION.commit()
    try:
        func()
    finally:
        if manual:
            update_job_by_id('job_manual', name, {'manual': False})
            SESSION.commit()


# ## INITIALIZE

bp.before_app_first_request(_initialize)
