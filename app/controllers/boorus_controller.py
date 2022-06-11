# APP/CONTROLLERS/BOORUS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, redirect, url_for, flash
from sqlalchemy.orm import selectinload
from wtforms import TextAreaField, IntegerField, StringField, BooleanField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS
from ..models import Booru
from ..logical.utility import set_error
from ..logical.database.booru_db import create_booru_from_parameters, update_booru_from_parameters
from ..logical.records.booru_rec import create_booru_from_source, update_booru_from_source,\
    update_booru_artists_from_source, archive_booru_for_deletion
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_or_abort, get_or_error, get_data_params,\
    check_param_requirements, nullify_blanks, get_form, parse_array_parameter, parse_bool_parameter,\
    set_default


# ## GLOBAL VARIABLES

bp = Blueprint("booru", __name__)


CREATE_REQUIRED_PARAMS = ['danbooru_id', 'current_name', 'deleted', 'banned']
VALUES_MAP = {
    'names': 'names',
    'name_string': 'names',
    **{k: k for k in Booru.__table__.columns.keys()},
}


# #### Load options

SHOW_HTML_OPTIONS = (
    selectinload(Booru._names),
    selectinload(Booru.artists),
)

INDEX_HTML_OPTIONS = (
    selectinload(Booru._names),
)

JSON_OPTIONS = (
    selectinload(Booru._names),
    selectinload(Booru.artists),
)


# #### Form

FORM_CONFIG = {
    'danbooru_id': {
        'name': 'Danbooru ID',
        'field': IntegerField,
        'kwargs': {
            'validators': [DataRequired()],
        },
    },
    'current_name': {
        'field': StringField,
    },
    'banned': {
        'field': BooleanField,
    },
    'deleted': {
        'field': BooleanField,
    },
    'name_string': {
        'name': 'Names',
        'field': TextAreaField,
        'kwargs': {
            'description': "Separated by whitespace.",
        },
    },
}


# ## FUNCTIONS

# #### Helper functions

def get_booru_form(**kwargs):
    return get_form('booru', FORM_CONFIG, **kwargs)


def uniqueness_check(dataparams, artist):
    danbooru_id = dataparams['danbooru_id'] if 'danbooru_id' in dataparams else artist.danbooru_id
    if danbooru_id != artist.danbooru_id:
        return Booru.query.filter_by(danbooru_id=danbooru_id).first()


def convert_data_params(dataparams):
    params = get_booru_form(**dataparams).data
    params['names'] = [name.lower() for name in parse_array_parameter(dataparams, 'names', 'name_string', r'\s')]
    params['current_name'] = params['current_name'].lower()
    params['banned'] = parse_bool_parameter(dataparams, 'banned')
    params['deleted'] = parse_bool_parameter(dataparams, 'deleted')
    params = nullify_blanks(params)
    return params


def convert_create_params(dataparams):
    createparams = convert_data_params(dataparams)
    set_default(createparams, 'banned', False)
    set_default(createparams, 'deleted', False)
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
    q = Booru.query
    q = search_filter(q, search)
    q = default_order(q, search)
    return q


def create():
    dataparams = get_data_params(request, 'booru')
    createparams = convert_create_params(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = check_param_requirements(createparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    check_booru = uniqueness_check(createparams, Booru())
    if check_booru is not None:
        retdata['item'] = check_booru.to_json()
        return set_error(retdata, "Booru already exists: booru #%d" % check_booru.id)
    booru = create_booru_from_parameters(createparams)
    retdata['item'] = booru.to_json()
    return retdata


def update(booru):
    dataparams = get_data_params(request, 'booru')
    updateparams = convert_update_params(dataparams)
    retdata = {'error': False, 'data': updateparams, 'params': dataparams}
    check_booru = uniqueness_check(updateparams, booru)
    if check_booru is not None:
        retdata['item'] = check_booru.to_json()
        return set_error(retdata, "Booru already exists: booru #%d" % check_booru.id)
    update_booru_from_parameters(booru, updateparams)
    retdata['item'] = booru.to_json()
    return retdata


def query_create():
    params = dict(danbooru_id=request.values.get('danbooru_id', type=int))
    retdata = {'error': False, 'params': params}
    if params['danbooru_id'] is None:
        return set_error(retdata, "Must include the Danbooru ID.")
    check_booru = uniqueness_check(params, Booru())
    if check_booru is not None:
        retdata['item'] = check_booru.to_json()
        return set_error(retdata, "Booru already exists: booru #%d" % check_booru.id)
    retdata.update(create_booru_from_source(params['danbooru_id']))
    return retdata


# #### Route functions

# ###### SHOW

@bp.route('/boorus/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(Booru, id, options=SHOW_HTML_OPTIONS)


@bp.route('/boorus/<int:id>', methods=['GET'])
def show_html(id):
    booru = get_or_abort(Booru, id, options=SHOW_HTML_OPTIONS)
    return render_template("boorus/show.html", booru=booru)


# ###### INDEX

@bp.route('/boorus.json', methods=['GET'])
def index_json():
    q = index()
    q = q.options(JSON_OPTIONS)
    return index_json_response(q, request)


@bp.route('/boorus', methods=['GET'])
def index_html():
    q = index()
    q = q.options(INDEX_HTML_OPTIONS)
    boorus = paginate(q, request)
    return render_template("boorus/index.html", boorus=boorus, booru=Booru())


# ###### CREATE

@bp.route('/boorus/new', methods=['GET'])
def new_html():
    """HTML access point to create function."""
    form = get_booru_form()
    return render_template("boorus/new.html", form=form, booru=Booru())


@bp.route('/boorus', methods=['POST'])
def create_html():
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('booru.new_html', **results['data']))
    return redirect(url_for('booru.show_html', id=results['item']['id']))


@bp.route('/boorus.json', methods=['POST'])
def create_json():
    return create()


# ###### UPDATE

@bp.route('/boorus/<int:id>/edit', methods=['GET'])
def edit_html(id):
    """HTML access point to update function."""
    booru = get_or_abort(Booru, id)
    editparams = booru.to_json()
    editparams['name_string'] = '\r\n'.join(booru.names)
    form = get_booru_form(**editparams)
    return render_template("boorus/edit.html", form=form, booru=booru)


@bp.route('/boorus/<int:id>', methods=['PUT'])
def update_html(id):
    booru = get_or_abort(Booru, id)
    results = update(booru)
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('booru.edit_html', id=booru.id))
    return redirect(url_for('booru.show_html', id=booru.id))


@bp.route('/boorus/<int:id>', methods=['PUT'])
def update_json(id):
    booru = get_or_error(Booru, id)
    if type(booru) is dict:
        return booru
    return update(booru)


# ###### DELETE

@bp.route('/boorus/<int:id>', methods=['DELETE'])
def delete_html(id):
    booru = get_or_abort(Booru, id)
    results = archive_booru_for_deletion(booru)
    if results['error']:
        flash(results['message'], 'error')
        return redirect(request.referrer)
    flash("Booru deleted.")
    return redirect(url_for('booru.index_html'))


# ###### MISC

@bp.route('/boorus/query_create', methods=['POST'])
def query_create_html():
    results = query_create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(request.referrer)
    else:
        flash("Booru created.")
    return redirect(url_for('booru.show_html', id=results['item']['id']))


@bp.route('/boorus/<int:id>/query_update', methods=['POST'])
def query_update_html(id):
    booru = get_or_abort(Booru, id)
    results = update_booru_from_source(booru)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash("Booru updated.")
    return redirect(url_for('booru.show_html', id=id))


@bp.route('/boorus/<int:id>/check_artists', methods=['POST'])
def check_artists_html(id):
    booru = get_or_abort(Booru, id)
    results = update_booru_artists_from_source(booru)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash("Booru updated.")
    return redirect(url_for('booru.show_html', id=id))
