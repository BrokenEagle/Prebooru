# APP/CONTROLLERS/ARTISTS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, redirect, url_for, flash
from sqlalchemy.orm import selectinload
from wtforms import TextAreaField, IntegerField, BooleanField, SelectField, StringField
from wtforms.validators import DataRequired

# ## PACKAGE IMPORTS
from utility.data import str_or_blank

# ## LOCAL IMPORTS
from .. import SCHEDULER
from ..models import Artist, Booru, SiteDescriptor
from ..logical.utility import set_error
from ..logical.sources import source_by_site_name
from ..logical.sources.base_src import get_artist_required_params
from ..logical.sources.danbooru_src import get_artists_by_url
from ..logical.records.artist_rec import update_artist_from_source, archive_artist_for_deletion,\
    artist_delete_site_account, artist_swap_site_account, artist_delete_name, artist_swap_name,\
    artist_delete_profile, artist_swap_profile, delete_artist, save_artist_to_archive
from ..logical.records.post_rec import check_artist_posts_for_danbooru_id
from ..logical.database.artist_db import create_artist_from_parameters, update_artist_from_parameters,\
    artist_append_booru
from ..logical.database.booru_db import create_booru_from_parameters
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_data_params, get_form, get_or_abort, get_or_error,\
    check_param_requirements, nullify_blanks, set_default, parse_bool_parameter,\
    hide_input, index_html_response, parse_array_parameter


# ## GLOBAL VARIABLES

bp = Blueprint("artist", __name__)

REQUIRED_PARAMS = ['site_name', 'site_artist_id', 'site_account']
VALUES_MAP = {
    'site_name': 'site_name',
    'site_account': 'site_account',
    'name': 'name',
    'profile': 'profile',
    'webpages': 'webpages',
    'webpage_string': 'webpages',
    **{k: k for k in Artist.__table__.columns.keys()},
}

# #### Load options

SHOW_HTML_OPTIONS = (
    selectinload(Artist.site_account),
    selectinload(Artist.name),
    selectinload(Artist.profile),
    selectinload(Artist.webpages),
    selectinload(Artist.notations),
    selectinload(Artist.boorus),
)

INDEX_HTML_OPTIONS = (
    selectinload(Artist.site_account),
    selectinload(Artist.name),
    selectinload(Artist.webpages),
)

JSON_OPTIONS = (
    selectinload(Artist.site_account),
    selectinload(Artist.name),
    selectinload(Artist.profile),
    selectinload(Artist.webpages),
)


# #### Form

FORM_CONFIG = {
    'site_name': {
        'field': SelectField,
        'kwargs': {
            'choices': [
                ("", ""),
                (SiteDescriptor.pixiv.name, SiteDescriptor.pixiv.name.title()),
                (SiteDescriptor.twitter.name, SiteDescriptor.twitter.name.title()),
                (SiteDescriptor.custom.name, SiteDescriptor.custom.name.title()),
            ],
            'validators': [DataRequired()],
            'coerce': str_or_blank,
        },
    },
    'site_artist_id': {
        'name': 'Site Artist ID',
        'field': IntegerField,
        'kwargs': {
            'validators': [DataRequired()],
        },
    },
    'site_created': {
        'field': StringField,
        'kwargs': {
            'description': "Format must be ISO8601 timestamp (e.g. 2021-05-24T04:46:51).",
        },
    },
    'site_account': {
        'name': 'Site Account',
        'field': StringField,
        'kwargs': {
            'validators': [DataRequired()],
        },
    },
    'name': {
        'name': 'Name',
        'field': StringField,
    },
    'webpage_string': {
        'name': 'Webpages',
        'field': TextAreaField,
        'kwargs': {
            'description': "Separated by carriage returns. Prepend with '-' to mark as inactive.",
        },
    },
    'profile': {
        'name': 'Profile',
        'field': TextAreaField,
    },
    'active': {
        'field': BooleanField,
        'kwargs': {
            'default': True,
        },
    },
    'primary': {
        'field': BooleanField,
        'kwargs': {
            'default': True,
        },
    },
}


# ## FUNCTIONS

# #### Helper functions

def get_artist_form(**kwargs):
    return get_form('artist', FORM_CONFIG, **kwargs)


def uniqueness_check(dataparams, artist):
    site_name = dataparams.get('site_name', artist.site_name)
    site_artist_id = dataparams.get('site_artist_id', artist.site_artist_id)
    if site_name != artist.site_name or site_artist_id != artist.site_artist_id:
        return Artist.query.filter(Artist.site_value == site_name,
                                   Artist.site_artist_id == site_artist_id)\
                           .one_or_none()


def convert_data_params(dataparams):
    params = get_artist_form(**dataparams).data
    params['active'] = parse_bool_parameter(dataparams, 'active')
    params['primary'] = parse_bool_parameter(dataparams, 'primary')
    params['webpages'] = parse_array_parameter(dataparams, 'webpages', 'webpage_string', r'\r?\n')
    params = nullify_blanks(params)
    return params


def convert_create_params(dataparams):
    createparams = convert_data_params(dataparams)
    set_default(createparams, 'active', True)
    set_default(createparams, 'primary', True)
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
    q = Artist.query
    q = search_filter(q, search)
    q = default_order(q, search)
    return q


def create():
    dataparams = get_data_params(request, 'artist')
    createparams = convert_create_params(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = check_param_requirements(createparams, REQUIRED_PARAMS, 'create')
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    check_artist = uniqueness_check(createparams, Artist())
    if check_artist is not None:
        retdata['item'] = check_artist.to_json()
        return set_error(retdata, "Artist already exists: artist #%d" % check_artist.id)
    artist = create_artist_from_parameters(createparams)
    retdata['item'] = artist.to_json()
    return retdata


def update(artist):
    dataparams = get_data_params(request, 'artist')
    updateparams = convert_update_params(dataparams)
    retdata = {'error': False, 'data': updateparams, 'params': dataparams}
    errors = check_param_requirements(updateparams, REQUIRED_PARAMS, 'update')
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    check_artist = uniqueness_check(updateparams, artist)
    if check_artist is not None:
        retdata['item'] = check_artist.to_json()
        return set_error(retdata, "Artist already exists: artist #%d" % check_artist.id)
    update_artist_from_parameters(artist, updateparams)
    retdata['item'] = artist.to_json()
    return retdata


def query_create():
    """Query source and create artist."""
    params = dict(url=request.values.get('url'))
    retdata = {'error': False, 'params': params}
    retdata.update(get_artist_required_params(params['url']))
    if retdata['error']:
        return retdata
    check_artist = uniqueness_check(retdata, Artist())
    if check_artist is not None:
        retdata['item'] = check_artist.to_json()
        return set_error(retdata, "Artist already exists: artist #%d" % check_artist.id)
    source = source_by_site_name(retdata['site_name'])
    createparams = retdata['data'] = source.get_artist_data(retdata['site_artist_id'])
    if not createparams['active']:
        return set_error(retdata, "Artist account does not exist!")
    artist = create_artist_from_parameters(createparams)
    retdata['item'] = artist.to_json()
    return retdata


def query_booru(artist):
    source = artist.source
    search_url = source.artist_booru_search_url(artist)
    artist_data = get_artists_by_url(search_url)
    if artist_data['error']:
        return artist_data
    existing_booru_ids = [booru.id for booru in artist.boorus]
    for data in artist_data['artists']:
        booru = Booru.query.filter_by(danbooru_id=data['id']).one_or_none()
        if booru is None:
            params = \
                {
                    'danbooru_id': data['id'],
                    'name': data['name'],
                    'banned': data['is_banned'],
                    'deleted': data['is_deleted'],
                }
            booru = create_booru_from_parameters(params)
        if booru.id not in existing_booru_ids:
            artist_append_booru(artist, booru)
    return {'error': False, 'artist': artist, 'boorus': artist.boorus}


def delete_site_account(artist):
    label_id = request.values.get('label_id', type=int)
    retdata = {'error': False, 'params': {'label_id': label_id}}
    if label_id is None:
        return set_error(retdata, "Description ID not set or a bad value.")
    retdata.update(artist_delete_site_account(artist, label_id))
    return retdata


def swap_site_account(artist):
    label_id = request.values.get('label_id', type=int)
    retdata = {'error': False, 'params': {'label_id': label_id}}
    if label_id is None:
        return set_error(retdata, "Label ID not set or a bad value.")
    retdata.update(artist_swap_site_account(artist, label_id))
    return retdata


def delete_name(artist):
    label_id = request.values.get('label_id', type=int)
    retdata = {'error': False, 'params': {'label_id': label_id}}
    if label_id is None:
        return set_error(retdata, "Label ID not set or a bad value.")
    retdata.update(artist_delete_name(artist, label_id))
    return retdata


def swap_name(artist):
    label_id = request.values.get('label_id', type=int)
    retdata = {'error': False, 'params': {'label_id': label_id}}
    if label_id is None:
        return set_error(retdata, "Description ID not set or a bad value.")
    retdata.update(artist_swap_name(artist, label_id))
    return retdata


def delete_profile(artist):
    description_id = request.values.get('description_id', type=int)
    retdata = {'error': False, 'params': {'description_id': description_id}}
    if description_id is None:
        return set_error(retdata, "Description ID not set or a bad value.")
    retdata.update(artist_delete_profile(artist, description_id))
    return retdata


def swap_profile(artist):
    description_id = request.values.get('description_id', type=int)
    retdata = {'error': False, 'params': {'description_id': description_id}}
    if description_id is None:
        return set_error(retdata, "Description ID not set or a bad value.")
    retdata.update(artist_swap_profile(artist, description_id))
    return retdata


# #### Route functions

# ###### SHOW

@bp.route('/artists/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(Artist, id, options=JSON_OPTIONS)


@bp.route('/artists/<int:id>', methods=['GET'])
def show_html(id):
    artist = get_or_abort(Artist, id, options=SHOW_HTML_OPTIONS)
    return render_template("artists/show.html", artist=artist)


# ###### INDEX

@bp.route('/artists.json', methods=['GET'])
def index_json():
    q = index()
    q = q.options(JSON_OPTIONS)
    return index_json_response(q, request)


@bp.route('/artists', methods=['GET'])
def index_html():
    q = index()
    q = q.options(INDEX_HTML_OPTIONS)
    page = paginate(q, request)
    return index_html_response(page, 'artist', 'artists')


# ###### CREATE

@bp.route('/artists/new', methods=['GET'])
def new_html():
    """HTML access point to create function."""
    form = get_artist_form(**request.args)
    return render_template("artists/new.html", form=form, artist=Artist())


@bp.route('/artists', methods=['POST'])
def create_html():
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('artist.new_html', **results['data']))
    return redirect(url_for('artist.show_html', id=results['item']['id']))


@bp.route('/artists.json', methods=['POST'])
def create_json():
    return create()


# ###### UPDATE

@bp.route('/artists/<int:id>/edit', methods=['GET'])
def edit_html(id):
    """HTML access point to update function."""
    artist = get_or_abort(Artist, id)
    editparams = artist.basic_json()
    editparams['site_name'] = artist.site_name
    editparams['site_account'] = artist.site_account_value
    editparams['name'] = artist.name_value
    marked_urls = ((('' if webpage.active else '-') + webpage.url) for webpage in artist.webpages)
    editparams['webpage_string'] = '\r\n'.join(marked_urls)
    editparams['profile'] = artist.profile_body
    form = get_artist_form(**editparams)
    if artist.illust_count > 0:
        # Artists with illusts cannot have their critical identifiers changed
        hide_input(form, 'site_name')
    return render_template("artists/edit.html", form=form, artist=artist)


@bp.route('/artists/<int:id>', methods=['PUT'])
def update_html(id):
    artist = get_or_abort(Artist, id)
    results = update(artist)
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('artist.edit_html', id=artist.id))
    return redirect(url_for('artist.show_html', id=artist.id))


@bp.route('/artists/<int:id>.json', methods=['PUT'])
def update_json(id):
    artist = get_or_error(Artist, id)
    if type(artist) is dict:
        return artist
    return update(artist)


# ###### DELETE

@bp.route('/artists/<int:id>/archive', methods=['DELETE'])
def soft_delete_html(id):
    artist = get_or_abort(Artist, id)
    results = archive_artist_for_deletion(artist)
    if results['error']:
        flash(results['message'], 'error')
        if not results['is_deleted']:
            return redirect(request.referrer)
    if results['is_deleted']:
        flash("Artist deleted.")
    return redirect(url_for('archive.show_html', id=results['item']['id']))


@bp.route('/artists/<int:id>', methods=['DELETE'])
def hard_delete_html(id):
    artist = get_or_abort(Artist, id)
    results = delete_artist(artist)
    if results['error']:
        flash(results['message'], 'error')
        if not results['is_deleted']:
            return redirect(request.referrer)
    if results['is_deleted']:
        flash("Artist deleted.")
    return redirect(url_for('artist.index_html'))


# ###### MISC

@bp.route('/artists/<int:id>/archive', methods=['POST'])
def archive_artist_html(id):
    artist = get_or_abort(Artist, id)
    results = save_artist_to_archive(artist, None)
    if results['error']:
        flash(results['message'], 'error')
        return redirect(request.referrer)
    flash("Artist archived.")
    return redirect(url_for('archive.show_html', id=results['item']['id']))


@bp.route('/artists/query_create', methods=['POST'])
def query_create_html():
    """Query source and create artist."""
    results = query_create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(request.referrer)
    flash('Artist created.')
    return redirect(url_for('artist.show_html', id=results['item']['id']))


@bp.route('/artists/query_create.json', methods=['POST'])
def query_create_json():
    return query_create()


@bp.route('/artists/<int:id>/query_update', methods=['POST'])
def query_update_html(id):
    """Query source and update artist."""
    artist = get_or_abort(Artist, id)
    update_artist_from_source(artist)
    flash("Artist updated.")
    return redirect(url_for('artist.show_html', id=id))


@bp.route('/artists/<int:id>/query_booru', methods=['POST'])
def query_booru_html(id):
    """Query booru and create/update booru relationships."""
    artist = get_or_abort(Artist, id)
    response = query_booru(artist)
    if response['error']:
        flash(response['message'])
    else:
        flash('Artist updated.')
    return redirect(url_for('artist.show_html', id=id))


@bp.route('/artists/<int:id>/account', methods=['DELETE'])
def delete_account_html(id):
    artist = get_or_abort(Artist, id)
    results = delete_site_account(artist)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash('Profile deleted.')
    return redirect(request.referrer)


@bp.route('/artists/<int:id>/account', methods=['PUT'])
def swap_account_html(id):
    artist = get_or_abort(Artist, id)
    results = swap_site_account(artist)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash('Profile swapped.')
    return redirect(request.referrer)


@bp.route('/artists/<int:id>/name', methods=['DELETE'])
def delete_name_html(id):
    artist = get_or_abort(Artist, id)
    results = delete_name(artist)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash('Profile deleted.')
    return redirect(request.referrer)


@bp.route('/artists/<int:id>/name', methods=['PUT'])
def swap_name_html(id):
    artist = get_or_abort(Artist, id)
    results = swap_name(artist)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash('Profile swapped.')
    return redirect(request.referrer)


@bp.route('/artists/<int:id>/profile', methods=['DELETE'])
def delete_profile_html(id):
    artist = get_or_abort(Artist, id)
    results = delete_profile(artist)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash('Profile deleted.')
    return redirect(request.referrer)


@bp.route('/artists/<int:id>/profile', methods=['PUT'])
def swap_profile_html(id):
    artist = get_or_abort(Artist, id)
    results = swap_profile(artist)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash('Profile swapped.')
    return redirect(request.referrer)


@bp.route('/artists/<int:id>/check_posts', methods=['POST'])
def check_posts_html(id):
    get_or_abort(Artist, id)
    SCHEDULER.add_job("check_artist_posts_for_danbooru_id-%d" % id, check_artist_posts_for_danbooru_id, args=(id,))
    flash('Job started.')
    return redirect(url_for('artist.show_html', id=id))


@bp.route('/artists/<int:id>/accounts', methods=['GET'])
def accounts_html(id):
    artist = get_or_abort(Artist, id)
    return render_template("artists/accounts.html", artist=artist)


@bp.route('/artists/<int:id>/names', methods=['GET'])
def names_html(id):
    artist = get_or_abort(Artist, id)
    return render_template("artists/names.html", artist=artist)


@bp.route('/artists/<int:id>/profiles', methods=['GET'])
def profiles_html(id):
    artist = get_or_abort(Artist, id)
    return render_template("artists/profiles.html", artist=artist)
