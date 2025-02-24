# APP/CONTROLLERS/BOORUS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, redirect, url_for, flash
from sqlalchemy.orm import selectinload
from wtforms import IntegerField, StringField, BooleanField

# ## LOCAL IMPORTS
from ..models import Booru, Artist
from ..logical.utility import set_error
from ..logical.database.booru_db import create_booru_from_parameters, update_booru_from_parameters,\
    booru_append_artist, booru_remove_artist
from ..logical.records.booru_rec import create_booru_from_source, update_booru_from_source,\
    update_booru_artists_from_source, archive_booru_for_deletion, booru_delete_name, booru_swap_name,\
    delete_booru, save_booru_to_archive
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_or_abort, get_or_error, get_data_params,\
    check_param_requirements, nullify_blanks, get_form, parse_bool_parameter, set_default, index_html_response


# ## GLOBAL VARIABLES

bp = Blueprint("booru", __name__)


CREATE_REQUIRED_PARAMS = ['name', 'deleted', 'banned']
VALUES_MAP = {
    'name': 'name',
    **{k: k for k in Booru.__table__.columns.keys()},
}

DEFAULT_DELETE_EXPIRES = 30  # Days

# #### Load options

SHOW_HTML_OPTIONS = (
    selectinload(Booru.name),
    selectinload(Booru.artists),
)

INDEX_HTML_OPTIONS = (
    selectinload(Booru.name),
)

JSON_OPTIONS = (
    selectinload(Booru.name),
    selectinload(Booru.artists),
)


# #### Form

FORM_CONFIG = {
    'danbooru_id': {
        'name': 'Danbooru ID',
        'field': IntegerField,
        'kwargs': {
            'description': "Leave blank for boorus which don't exist on Danbooru.",
        },
    },
    'name': {
        'field': StringField,
    },
    'banned': {
        'field': BooleanField,
    },
    'deleted': {
        'field': BooleanField,
    },
}


# ## FUNCTIONS

# #### Helper functions

def get_booru_form(**kwargs):
    return get_form('booru', FORM_CONFIG, **kwargs)


def uniqueness_check(dataparams, artist):
    danbooru_id = dataparams.get('danbooru_id', artist.danbooru_id)
    if danbooru_id is not None and danbooru_id != artist.danbooru_id:
        return Booru.query.filter_by(danbooru_id=danbooru_id).one_or_none()


def convert_data_params(dataparams):
    params = get_booru_form(**dataparams).data
    params['name'] = params['name'].lower()
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


def delete_name(booru):
    label_id = request.values.get('label_id', type=int)
    retdata = {'error': False, 'params': {'label_id': label_id}}
    if label_id is None:
        return set_error(retdata, "Label ID not set or a bad value.")
    retdata.update(booru_delete_name(booru, label_id))
    return retdata


def swap_name(booru):
    label_id = request.values.get('label_id', type=int)
    retdata = {'error': False, 'params': {'label_id': label_id}}
    if label_id is None:
        return set_error(retdata, "Description ID not set or a bad value.")
    retdata.update(booru_swap_name(booru, label_id))
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
    page = paginate(q, request)
    return index_html_response(page, 'booru', 'boorus')


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
    editparams['name'] = booru.name_value
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

@bp.route('/boorus/<int:id>/archive', methods=['DELETE'])
def soft_delete_html(id):
    booru = get_or_abort(Booru, id)
    expires = request.values.get('expires', DEFAULT_DELETE_EXPIRES, type=int)
    results = archive_booru_for_deletion(booru, expires)
    if results['error']:
        flash(results['message'], 'error')
        if not results['is_deleted']:
            return redirect(request.referrer)
    if results['is_deleted']:
        flash("Booru deleted.")
    return redirect(url_for('archive.show_html', id=results['item']['id']))


@bp.route('/boorus/<int:id>', methods=['DELETE'])
def hard_delete_html(id):
    booru = get_or_abort(Booru, id)
    results = delete_booru(booru)
    if results['error']:
        flash(results['message'], 'error')
        if not results['is_deleted']:
            return redirect(request.referrer)
    if results['is_deleted']:
        flash("Booru deleted.")
    return redirect(url_for('booru.index_html'))


# ###### MISC

@bp.route('/boorus/<int:id>/archive', methods=['POST'])
def archive_booru_html(id):
    booru = get_or_abort(Booru, id)
    results = save_booru_to_archive(booru, None)
    if results['error']:
        flash(results['message'], 'error')
        return redirect(request.referrer)
    flash("Booru archived.")
    return redirect(url_for('archive.show_html', id=results['item']['id']))


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


@bp.route('/boorus/<int:id>/name', methods=['DELETE'])
def delete_name_html(id):
    booru = get_or_abort(Booru, id)
    results = delete_name(booru)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash('Profile deleted.')
    return redirect(request.referrer)


@bp.route('/boorus/<int:id>/name', methods=['PUT'])
def swap_name_html(id):
    booru = get_or_abort(Booru, id)
    results = swap_name(booru)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash('Profile swapped.')
    return redirect(request.referrer)


@bp.route('/boorus/<int:id>/check_artists', methods=['POST'])
def check_artists_html(id):
    booru = get_or_abort(Booru, id)
    results = update_booru_artists_from_source(booru)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash("Booru updated.")
    return redirect(url_for('booru.show_html', id=id))


@bp.route('/boorus/<int:id>/add_artist', methods=['POST'])
def add_artist_html(id):
    booru = get_or_abort(Booru, id)
    artist_id = request.values.get('artist_id', type=int)
    artist = Artist.find(artist_id)
    if artist is not None:
        if artist.id not in booru.artist_ids:
            booru_append_artist(booru, artist)
            flash("Artist added.")
        else:
            flash(f'{artist.shortlink} already added to {booru.shortlink}.', 'error')
    else:
        flash(f'artist #{artist_id} not found.', 'error')
    return redirect(url_for('booru.show_html', id=id))


@bp.route('/boorus/<int:id>/remove_artist', methods=['DELETE'])
def remove_artist_html(id):
    booru = get_or_abort(Booru, id)
    artist_id = request.values.get('artist_id', type=int)
    artist = Artist.find(artist_id)
    if artist is not None:
        if artist.id in booru.artist_ids:
            booru_remove_artist(booru, artist)
            flash("Artist removed.")
        else:
            flash(f'{artist.shortlink} not associated with {booru.shortlink}.')
    else:
        flash(f'artist #{artist_id} not found.')
    return redirect(url_for('booru.show_html', id=id))


@bp.route('/boorus/<int:id>/names', methods=['GET'])
def names_html(id):
    booru = get_or_abort(Booru, id)
    return render_template("boorus/names.html", booru=booru)
