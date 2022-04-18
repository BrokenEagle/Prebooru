# APP/CONTROLLERS/SUBSCRIPTION_POOLS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, abort, url_for, flash, redirect
from wtforms import BooleanField, FloatField, IntegerField
from wtforms.validators import DataRequired


# ## LOCAL IMPORTS
from .. import SCHEDULER
from ..models import SubscriptionPool, Artist
from ..logical.utility import set_error
from ..logical.tasks.worker import process_subscription
from ..logical.database.subscription_pool_db import create_subscription_pool_from_parameters,\
    update_subscription_pool_from_parameters, update_subscription_pool_status
from ..logical.database.jobs_db import get_job_status_data, check_job_status_exists, create_job_status,\
    update_job_status
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_data_params, CustomNameForm, get_or_abort, get_or_error,\
    check_param_requirements, nullify_blanks, parse_bool_parameter, set_default, hide_input, parse_type


# ## GLOBAL VARIABLES

bp = Blueprint("subscription_pool", __name__)

CREATE_REQUIRED_PARAMS = ['artist_id']
VALUES_MAP = {
    **{k: k for k in SubscriptionPool.__table__.columns.keys()},
}


# ## CLASSES

def get_subscription_pool_form(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class SubscriptionPoolForm(CustomNameForm):
        artist_id = IntegerField('Artist ID', id='subscription-pool-artist-id',
                                 custom_name='subscription_pool[artist_id]', validators=[DataRequired()])
        interval = FloatField('Interval', id='subscription-pool-interval',
                              custom_name='subscription_pool[interval]',
                              description="How often to check the artist (hours, >1.0).")
        expiration = FloatField('Expiration', id='subscription-pool-expiration',
                                custom_name='subscription_pool[expiration]',
                                description="""How long to wait before deleting the post/illust (days, >1.0).
                                               Clear the field for no expiration.""")
        active = BooleanField('Active', id='subscription-pool-active',
                              custom_name='subscription_pool[active]', default=True)
    return SubscriptionPoolForm(**kwargs)


# ## FUNCTIONS

# #### Helper functions

def parameter_validation(dataparams):
    errors = []
    if dataparams['interval'] < 1.0:
        errors.append("Interval must be greater than 1.0 hours.")
    if dataparams['expiration'] is not None and dataparams['expiration'] < 1.0:
        errors.append("Expiration must be greater than 1.0 days if it exists.")
    return errors


def convert_data_params(dataparams):
    params = get_subscription_pool_form(**dataparams).data
    params['interval'] = parse_type(params, 'interval', float)
    params['expiration'] = parse_type(params, 'expiration', float)
    params['active'] = parse_bool_parameter(dataparams, 'active')
    params = nullify_blanks(params)
    return params


def convert_create_params(dataparams):
    createparams = convert_data_params(dataparams)
    set_default(createparams, 'interval', 24.0)
    set_default(createparams, 'active', True)
    return createparams


def convert_update_params(dataparams):
    updateparams = convert_data_params(dataparams)
    updatelist = [VALUES_MAP[key] for key in dataparams if key in VALUES_MAP]
    updateparams = {k: v for (k, v) in updateparams.items() if k in updatelist}
    return updateparams


# #### Route auxiliary functions

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = SubscriptionPool.query
    q = search_filter(q, search)
    q = default_order(q, search)
    return q


def create():
    dataparams = get_data_params(request, 'subscription_pool')
    createparams = convert_create_params(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = check_param_requirements(createparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    errors = parameter_validation(createparams)
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    subscription_pool = create_subscription_pool_from_parameters(createparams)
    retdata['item'] = subscription_pool.to_json()
    return retdata


def update(subscription_pool):
    dataparams = get_data_params(request, 'subscription_pool')
    updateparams = convert_update_params(dataparams)
    retdata = {'error': False, 'data': updateparams, 'params': dataparams}
    errors = parameter_validation(updateparams)
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    update_subscription_pool_from_parameters(subscription_pool, updateparams)
    retdata['item'] = subscription_pool.to_json()
    return retdata


# #### Route functions

# ###### SHOW

@bp.route('/subscription_pools/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(SubscriptionPool, id)


@bp.route('/subscription_pools/<int:id>', methods=['GET'])
def show_html(id):
    subscription_pool = get_or_abort(SubscriptionPool, id)
    job_id = request.args.get('job')
    job_status = get_job_status_data(job_id) if job_id else None
    return render_template("subscription_pools/show.html", subscription_pool=subscription_pool, job_status=job_status,
                           job_id=job_id)


# ###### INDEX

@bp.route('/subscription_pools.json', methods=['GET'])
def index_json():
    q = index()
    return index_json_response(q, request)


@bp.route('/subscription_pools', methods=['GET'])
def index_html():
    q = index()
    subscription_pools = paginate(q, request)
    return render_template("subscription_pools/index.html", subscription_pools=subscription_pools,
                           subscription_pool=SubscriptionPool())


# ###### CREATE

@bp.route('/subscription_pools/new', methods=['GET'])
def new_html():
    """HTML access point to create function."""
    form = get_subscription_pool_form(**request.args)
    artist = None
    if form.artist_id.data is not None:
        artist = Artist.find(form.artist_id.data)
        if artist is None:
            flash("Artist #%d not found." % form.artist_id.data, 'error')
            form.artist_id.data = None
        else:
            hide_input(form, 'artist_id', artist.id)
    return render_template("subscription_pools/new.html", form=form, subscription_pool=SubscriptionPool(),
                           artist=artist)


@bp.route('/subscription_pools', methods=['POST'])
def create_html():
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('subscription_pool.new_html', **results['data']))
    return redirect(url_for('subscription_pool.show_html', id=results['item']['id']))


@bp.route('/subscription_pools.json', methods=['POST'])
def create_json():
    return create()


# ###### UPDATE

@bp.route('/subscription_pools/<int:id>/edit', methods=['GET'])
def edit_html(id):
    subscription_pool = SubscriptionPool.find(id)
    if subscription_pool is None:
        abort(404)
    editparams = subscription_pool.to_json()
    form = get_subscription_pool_form(**editparams)
    hide_input(form, 'artist_id', subscription_pool.artist_id)
    return render_template("subscription_pools/edit.html", form=form, subscription_pool=subscription_pool)


@bp.route('/subscription_pools/<int:id>', methods=['PUT'])
def update_html(id):
    subscription_pool = get_or_abort(SubscriptionPool, id)
    results = update(subscription_pool)
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('subscription_pool.edit_html', id=id))
    return redirect(url_for('subscription_pool.show_html', id=subscription_pool.id))


@bp.route('/subscription_pools/<int:id>', methods=['PUT'])
def update_json(id):
    subscription_pool = get_or_error(SubscriptionPool, id)
    if type(subscription_pool) is dict:
        return subscription_pool
    return update(subscription_pool)


# ###### Misc

@bp.route('/subscription_pools/<int:id>/process', methods=['POST'])
def process_html(id):
    subscription_pool = get_or_abort(SubscriptionPool, id)
    if subscription_pool.status != 'idle':
        flash("Subscription currently processing.", 'error')
        return redirect(request.referrer)
    update_subscription_pool_status(subscription_pool, 'manual')
    job_id = "process_subscription-%d" % subscription_pool.id
    job_status = {
        'stage': None,
        'range': None,
        'records': 0,
        'illust_creates': 0,
        'illust_updates': 0,
        'elements': 0,
        'downloads': 0,
    }
    if check_job_status_exists(job_id):
        update_job_status(job_id, job_status)
    else:
        create_job_status(job_id, job_status)
    SCHEDULER.add_job(job_id, process_subscription, args=(subscription_pool.id, job_id))
    flash("Subscription started.")
    return redirect(url_for('subscription_pool.show_html', id=subscription_pool.id, job=job_id))


@bp.route('/subscription_pools/<int:id>/status.json', methods=['GET'])
def status_json(id):
    subscription_pool = get_or_error(SubscriptionPool, id)
    if type(subscription_pool) is dict:
        return subscription_pool
    job_id = request.args.get('job')
    if job_id is None:
        return {'error': True, 'message': "No Job ID parameter found."}
    job_status = get_job_status_data(job_id)
    if job_status is None:
        return {'error': True, 'message': "Job with ID %s not found." % job_id}
    return {'error': False, 'item': job_status}
