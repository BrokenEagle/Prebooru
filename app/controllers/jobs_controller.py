# APP/CONTROLLERS/JOBS_CONTROLLER.PY

# ## PYTHON IMPORTS
import datetime

# ## EXTERNAL IMPORTS
from flask import Blueprint, request
from flask_apscheduler.json import jsonify

# ## PACKAGE IMPORTS
from utility.time import local_timezone

# ## LOCAL IMPORTS
from .. import SCHEDULER


# ## GLOBAL VARIABLES

bp = Blueprint('job', __name__)


# ## FUNCTIONS

# #### INDEX

@bp.route('/jobs', methods=['GET'])
def index_json():
    data = []
    for job in SCHEDULER.get_jobs():
        data.append({
            'id': job.id,
            'name': job.name,
            'executor': job.executor,
            'func': job.func_ref,
            'misfire_grace_time': job.misfire_grace_time,
            'next_run_time': job.next_run_time.isoformat(),
            'pending': job.pending,
            })
    return jsonify(data)


# #### CREATE

@bp.route('/jobs', methods=['POST'])
def create_info_json():
    data = request.get_json(force=True)
    if 'id' not in data:
        return jsonify({'error': True, 'message': 'Missing parameter "id"'}, status=400)
    if SCHEDULER.get_job(data['id']) is not None:
        return jsonify({'error': True, 'message': 'Job %s already exists' % data['id']}, status=409)
    data['next_run_time'] = datetime.datetime.fromisoformat(data['next_run_time']).replace(tzinfo=local_timezone())
    try:
        job = SCHEDULER.add_job(**data)
    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}, status=500)
    return jsonify({'error': False, 'job': job})


# #### UDPATE

@bp.route('/jobs/<id>', methods=['PUT'])
def update_info_json(id):
    if SCHEDULER.get_job(id) is None:
        return jsonify({'error': True, 'message': 'Job %s not found' % id}, status=404)
    data = request.get_json(force=True)
    data['next_run_time'] = datetime.datetime.fromisoformat(data['next_run_time']).replace(tzinfo=local_timezone())
    try:
        SCHEDULER.modify_job(id, **data)
    except Exception as e:
        return jsonify({'error': True, 'message': str(e)}, status=500)
    job = SCHEDULER.get_job(id)
    return jsonify({'error': False, 'job': job})
