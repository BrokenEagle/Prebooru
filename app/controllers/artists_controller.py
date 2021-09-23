# APP\CONTROLLERS\ARTISTS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, redirect, url_for, flash
from sqlalchemy.orm import selectinload
from wtforms import TextAreaField, IntegerField, BooleanField, SelectField, StringField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS
from ..models import Artist, Booru
from ..logical.sources.base import get_source_by_id, get_artist_required_params
from ..logical.sources.danbooru import get_artists_by_url
from ..database.artist_db import create_artist_from_parameters, update_artist_from_parameters, update_artist_from_source, artist_append_booru,\
    artist_delete_profile
from ..database.booru_db import create_booru_from_parameters
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values, get_params_value, paginate,\
    default_order, get_data_params, CustomNameForm, get_or_abort, get_or_error, set_error, parse_array_parameter, check_param_requirements,\
    int_or_blank, nullify_blanks, set_default, parse_bool_parameter, hide_input


# ## GLOBAL VARIABLES

bp = Blueprint("artist", __name__)

CREATE_REQUIRED_PARAMS = ['site_id', 'site_artist_id']
VALUES_MAP = {
    'site_accounts': 'site_accounts',
    'site_account_string': 'site_accounts',
    'names': 'names',
    'name_string': 'names',
    'webpages': 'webpages',
    'webpage_string': 'webpages',
    'profiles': 'profiles',
    'profile': 'profiles',
    **{k: k for k in Artist.__table__.columns.keys()},
}


# #### Load options

SHOW_HTML_OPTIONS = (
    selectinload(Artist.site_accounts),
    selectinload(Artist.names),
    selectinload(Artist.profiles),
    selectinload(Artist.webpages),
    selectinload(Artist.notations),
    selectinload(Artist.boorus),
)

INDEX_HTML_OPTIONS = (
    selectinload(Artist.site_accounts),
    selectinload(Artist.names),
    selectinload(Artist.webpages),
    selectinload(Artist.notations),
)

JSON_OPTIONS = (
    selectinload(Artist.site_accounts),
    selectinload(Artist.names),
    selectinload(Artist.profiles),
    selectinload(Artist.webpages),
)


# #### Forms

def get_artist_form(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class ArtistForm(CustomNameForm):
        site_id = SelectField('Site', choices=[("", ""), (1, 'Pixiv'), (3, 'Twitter')], id='artist-site-id', custom_name='artist[site_id]', validators=[DataRequired()], coerce=int_or_blank)
        site_artist_id = IntegerField('Site Artist ID', id='artist-site-artist-id', custom_name='artist[site_artist_id]', validators=[DataRequired()])
        current_site_account = StringField('Current Site Account', id='artist-current-site-account', custom_name='artist[current_site_account]')
        site_created = StringField('Site Created', id='artist-site-created', custom_name='artist[site_created]', description='Format must be ISO8601 timestamp (e.g. 2021-05-24T04:46:51).')
        site_account_string = TextAreaField('Site Accounts', id='artist-site-account-string', custom_name='artist[site_account_string]', description="Separated by whitespace.")
        name_string = TextAreaField('Site Names', id='artist-name-string', custom_name='artist[name_string]', description="Separated by carriage returns.")
        webpage_string = TextAreaField('Webpages', id='artist-webpage-string', custom_name='artist[webpage_string]', description="Separated by carriage returns. Prepend with '-' to mark as inactive.")
        profile = TextAreaField('Profile', id='artist-profile', custom_name='artist[profile]')
        active = BooleanField('Active', id='artist-active', custom_name='artist[active]', default=True)
    return ArtistForm(**kwargs)


# ## FUNCTIONS

# #### Helper functions

def uniqueness_check(dataparams, artist):
    site_id = dataparams['site_id'] if 'site_id' in dataparams else artist.site_id
    site_artist_id = dataparams['site_artist_id'] if 'site_artist_id' in dataparams else artist.site_artist_id
    if site_id != artist.site_id or site_artist_id != artist.site_artist_id:
        return Artist.query.filter_by(site_id=site_id, site_artist_id=site_artist_id).first()


def convert_data_params(dataparams):
    params = get_artist_form(**dataparams).data
    params['site_accounts'] = parse_array_parameter(dataparams, 'site_accounts', 'site_account_string', r'\s')
    params['names'] = parse_array_parameter(dataparams, 'names', 'name_string', r'\r?\n')
    params['webpages'] = parse_array_parameter(dataparams, 'webpages', 'webpage_string', r'\r?\n')
    params['active'] = parse_bool_parameter(dataparams, 'active')
    params['profiles'] = params['profile']
    params = nullify_blanks(params)
    return params


def convert_create_params(dataparams):
    createparams = convert_data_params(dataparams)
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
    q = Artist.query
    q = search_filter(q, search)
    q = default_order(q, search)
    return q


def create():
    dataparams = get_data_params(request, 'artist')
    createparams = convert_create_params(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = check_param_requirements(createparams, CREATE_REQUIRED_PARAMS)
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
    source = get_source_by_id(retdata['site_id'])
    createparams = retdata['data'] = source.get_artist_data(retdata['site_artist_id'])
    if not createparams['active']:
        return set_error(retdata, "Artist account does not exist!")
    artist = create_artist_from_parameters(createparams)
    retdata['item'] = artist.to_json()
    return retdata


def query_booru(artist):
    source = get_source_by_id(artist.site_id)
    search_url = source.artist_booru_search_url(artist)
    artist_data = get_artists_by_url(search_url)
    if artist_data['error']:
        return artist_data
    existing_booru_ids = [booru.id for booru in artist.boorus]
    for danbooru_artist in artist_data['artists']:
        booru = Booru.query.filter_by(danbooru_id=danbooru_artist['id']).first()
        if booru is None:
            booru = create_booru_from_parameters({'danbooru_id': danbooru_artist['id'], 'current_name': danbooru_artist['name']})
        if booru.id not in existing_booru_ids:
            artist_append_booru(artist, booru)
    return {'error': False, 'artist': artist, 'boorus': artist.boorus}


def delete_profile(artist):
    description_id = request.values.get('description_id', type=int)
    retdata = {'error': False, 'params': {'description_id': description_id}}
    if description_id is None:
        return set_error(retdata, "Description ID not set or a bad value.")
    retdata.update(artist_delete_profile(artist, description_id))
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
    artists = paginate(q, request)
    return render_template("artists/index.html", artists=artists, artist=Artist())


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
    editparams = artist.to_json()
    editparams['site_account_string'] = '\r\n'.join(site_account.name for site_account in artist.site_accounts)
    editparams['name_string'] = '\r\n'.join(artist_name.name for artist_name in artist.names)
    editparams['webpage_string'] = '\r\n'.join((('' if webpage.active else '-') + webpage.url) for webpage in artist.webpages)
    form = get_artist_form(**editparams)
    if artist.illust_count > 0:
        # Artists with illusts cannot have their critical identifiers changed
        hide_input(form, 'site_id')
        hide_input(form, 'site_artist_id')
    return render_template("artists/edit.html", form=form, artist=artist)


@bp.route('/artists/<int:id>', methods=['PUT'])
def update_html(id):
    artist = get_or_abort(Artist, id)
    results = update(artist)
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('artist.edit_html', id=artist.id))
    return redirect(url_for('artist.show_html', id=artist.id))


@bp.route('/artists/<int:id>', methods=['PUT'])
def update_json(id):
    artist = get_or_error(Artist, id)
    if type(artist) is dict:
        return artist
    return update(artist)


# ###### MISC

@bp.route('/artists/query_create', methods=['POST'])
def query_create_html():
    """Query source and create artist."""
    results = query_create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(request.referrer)
    flash('Artist created.')
    return redirect(url_for('artist.show_html', id=results['item']['id']))


@bp.route('/artists/<int:id>/query_update', methods=['POST'])
def query_update_html(id):
    """Query source and update artist."""
    artist = get_or_abort(Artist, id)
    source = get_source_by_id(artist.site_id)
    update_artist_from_source(artist, source)
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


@bp.route('/artists/<int:id>/profile', methods=['DELETE'])
def delete_profile_html(id):
    artist = get_or_abort(Artist, id)
    results = delete_profile(artist)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash('Profile deleted.')
    return redirect(url_for('artist.show_html', id=id))
