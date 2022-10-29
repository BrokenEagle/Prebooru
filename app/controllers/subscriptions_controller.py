# APP/CONTROLLERS/SUBSCRIPTIONS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, abort, url_for, flash, redirect
from wtforms import BooleanField, FloatField, IntegerField
from wtforms.validators import DataRequired


# ## LOCAL IMPORTS
from .. import SCHEDULER, SESSION
from ..models import Subscription, Artist
from ..logical.utility import set_error
from ..logical.records.subscription_rec import process_subscription
from ..logical.database.subscription_db import create_subscription_from_parameters,\
    update_subscription_from_parameters, update_subscription_status, delay_subscription_elements,\
    delete_subscription
from ..logical.database.jobs_db import get_job_status_data, create_or_update_job_status
from ..logical.database.server_info_db import get_subscriptions_ready
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_data_params, get_form, get_or_abort, get_or_error,\
    check_param_requirements, nullify_blanks, parse_bool_parameter, set_default, hide_input, parse_type


# ## GLOBAL VARIABLES

bp = Blueprint("subscription", __name__)

CREATE_REQUIRED_PARAMS = ['artist_id']
VALUES_MAP = {
    **{k: k for k in Subscription.__table__.columns.keys()},
}


# #### Form

FORM_CONFIG = {
    'artist_id': {
        'name': 'Artist ID',
        'field': IntegerField,
        'kwargs': {
            'validators': [DataRequired()],
        },
    },
    'interval': {
        'field': FloatField,
        'kwargs': {
            'description': "How often to check the artist (hours, >1.0). [Default: 24 hours]",
        },
    },
    'expiration': {
        'field': FloatField,
        'kwargs': {
            'description': """How long to wait before deleting the post/illust (days, >1.0).
                              Clear the field for no expiration. [Default: no expiration]""",
        },
    },
    'active': {
        'field': BooleanField,
        'kwargs': {
            'default': True,
        },
    },
}


# ## FUNCTIONS

# #### Helper functions

def get_subscription_form(**kwargs):
    return get_form('subscription', FORM_CONFIG, **kwargs)


def parameter_validation(dataparams, is_update):
    errors = []
    if dataparams['interval'] < 1.0:
        errors.append("Interval must be greater than 1.0 hours.")
    if dataparams['expiration'] is not None and dataparams['expiration'] < 1.0:
        errors.append("Expiration must be greater than 1.0 days if it exists.")
    if is_update:
        return errors
    artist = Artist.find(dataparams['artist_id'])
    if artist is None:
        errors.append(f"Artist #{dataparams['artist_id']} does not exist.")
    elif artist.subscription is not None:
        errors.append(f"{artist.subscription.shortlink} already exists for {artist.shortlink}.")
    return errors


def convert_data_params(dataparams):
    params = get_subscription_form(**dataparams).data
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
    q = Subscription.query
    q = search_filter(q, search)
    q = default_order(q, search)
    return q


def create():
    dataparams = get_data_params(request, 'subscription')
    createparams = convert_create_params(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = check_param_requirements(createparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    errors = parameter_validation(createparams, False)
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    subscription = create_subscription_from_parameters(createparams)
    retdata['item'] = subscription.to_json()
    return retdata


def update(subscription):
    dataparams = get_data_params(request, 'subscription')
    updateparams = convert_update_params(dataparams)
    retdata = {'error': False, 'data': updateparams, 'params': dataparams}
    errors = parameter_validation(updateparams, True)
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    update_subscription_from_parameters(subscription, updateparams)
    retdata['item'] = subscription.to_json()
    return retdata


# #### Route functions

# ###### SHOW

@bp.route('/subscriptions/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(Subscription, id)


@bp.route('/subscriptions/<int:id>', methods=['GET'])
def show_html(id):
    subscription = get_or_abort(Subscription, id)
    job_id = request.args.get('job')
    job_status = get_job_status_data(job_id)
    return render_template("subscriptions/show.html", subscription=subscription, job_status=job_status,
                           job_id=job_id)


# ###### INDEX

@bp.route('/subscriptions.json', methods=['GET'])
def index_json():
    q = index()
    return index_json_response(q, request)


@bp.route('/subscriptions', methods=['GET'])
def index_html():
    q = index()
    subscriptions = paginate(q, request)
    return render_template("subscriptions/index.html", subscriptions=subscriptions,
                           subscription=Subscription())


# ###### CREATE

@bp.route('/subscriptions/new', methods=['GET'])
def new_html():
    """HTML access point to create function."""
    form = get_subscription_form(**request.args)
    artist = None
    if form.artist_id.data is not None:
        artist = Artist.find(form.artist_id.data)
        if artist is None:
            flash("Artist #%d not found." % form.artist_id.data, 'error')
            form.artist_id.data = None
        else:
            hide_input(form, 'artist_id', artist.id)
    return render_template("subscriptions/new.html", form=form, subscription=Subscription(),
                           artist=artist)


@bp.route('/subscriptions', methods=['POST'])
def create_html():
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('subscription.new_html', **results['data']))
    return redirect(url_for('subscription.show_html', id=results['item']['id']))


@bp.route('/subscriptions.json', methods=['POST'])
def create_json():
    return create()


# ###### UPDATE

@bp.route('/subscriptions/<int:id>/edit', methods=['GET'])
def edit_html(id):
    subscription = Subscription.find(id)
    if subscription is None:
        abort(404)
    editparams = subscription.to_json()
    form = get_subscription_form(**editparams)
    hide_input(form, 'artist_id', subscription.artist_id)
    return render_template("subscriptions/edit.html", form=form, subscription=subscription)


@bp.route('/subscriptions/<int:id>', methods=['PUT'])
def update_html(id):
    subscription = get_or_abort(Subscription, id)
    results = update(subscription)
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('subscription.edit_html', id=id))
    return redirect(url_for('subscription.show_html', id=subscription.id))


@bp.route('/subscriptions/<int:id>', methods=['PUT'])
def update_json(id):
    subscription = get_or_error(Subscription, id)
    if type(subscription) is dict:
        return subscription
    return update(subscription)


# ###### DELETE

@bp.route('/subscriptions/<int:id>', methods=['DELETE'])
def delete_html(id):
    subscription = get_or_abort(Subscription, id)
    artist = subscription.artist
    delete_subscription(subscription)
    flash("Subscription deleted.")
    return redirect(artist.show_url)


# ###### Misc

@bp.route('/subscriptions/<int:id>/process', methods=['POST'])
def process_html(id):
    if not get_subscriptions_ready():
        flash("Subscriptions not yet initialized.", 'error')
        return redirect(request.referrer)
    subscription = get_or_abort(Subscription, id)
    if subscription.status.name != 'idle':
        flash("Subscription currently processing.", 'error')
        return redirect(request.referrer)
    update_subscription_status(subscription, 'manual')
    job_id = "process_subscription-%d" % subscription.id
    job_status = {
        'stage': None,
        'range': None,
        'records': 0,
        'illusts': 0,
        'elements': 0,
        'downloads': 0,
    }
    create_or_update_job_status(job_id, job_status)
    SESSION.commit()
    SCHEDULER.add_job(job_id, process_subscription, args=(subscription.id, job_id))
    flash("Subscription started.")
    return redirect(url_for('subscription.show_html', id=subscription.id, job=job_id))


@bp.route('/subscriptions/<int:id>/reset', methods=['PUT'])
def reset_html(id):
    subscription = get_or_abort(Subscription, id)
    update_subscription_status(subscription, 'idle')
    return redirect(request.referrer)


@bp.route('/subscriptions/<int:id>/status.json', methods=['GET'])
def status_json(id):
    subscription = get_or_error(Subscription, id)
    if type(subscription) is dict:
        return subscription
    job_id = request.args.get('job')
    if job_id is None:
        return {'error': True, 'message': "No Job ID parameter found."}
    job_status = get_job_status_data(job_id)
    if job_status is None:
        return {'error': True, 'message': "Job with ID %s not found." % job_id}
    return {'error': False, 'item': job_status}


@bp.route('/subscriptions/<int:id>/delay', methods=['POST'])
def delay_html(id):
    subscription = get_or_abort(Subscription, id)
    delay_days = request.values.get('days', type=float)
    if delay_days is None:
        flash("No days parameter present.", 'error')
    else:
        delay_subscription_elements(subscription, delay_days)
        flash("Updated elements.")
    return redirect(request.referrer)
