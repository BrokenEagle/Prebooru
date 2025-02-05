# APP/CONTROLLERS/ILLUSTS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, redirect, url_for, flash
from sqlalchemy import not_, or_
from sqlalchemy.orm import selectinload
from wtforms import TextAreaField, IntegerField, BooleanField, SelectField, StringField
from wtforms.validators import DataRequired

# ## PACKAGE IMPORTS
from utility.data import eval_bool_string, is_falsey, str_or_blank

# ## LOCAL IMPORTS
from ..models import Illust, IllustUrl, Artist, Post, PoolIllust, PoolPost, SiteDescriptor
from ..logical.utility import set_error
from ..logical.sites import site_name_by_url
from ..logical.sources import source_by_site_name
from ..logical.records.artist_rec import get_or_create_artist_from_source
from ..logical.records.illust_rec import update_illust_from_source, archive_illust_for_deletion,\
    illust_delete_title, illust_swap_title, illust_delete_commentary, illust_swap_commentary,\
    illust_add_additional_commentary, delete_illust, save_illust_to_archive
from ..logical.sources.base_src import get_post_source
from ..logical.database.illust_db import create_illust_from_parameters, update_illust_from_parameters,\
    set_illust_artist
from .base_controller import get_params_value, process_request_values, show_json_response, index_json_response,\
    search_filter, default_order, paginate, get_data_params, get_form, get_or_abort, get_or_error,\
    hide_input, nullify_blanks, set_default, check_param_requirements, parse_array_parameter,\
    parse_bool_parameter, get_page, get_limit, index_html_response


# ## GLOBAL VARIABLES

bp = Blueprint("illust", __name__)

REQUIRED_PARAMS = ['site_name', 'site_illust_id']
VALUES_MAP = {
    'site_name': 'site_name',
    'illust_urls': 'illust_urls',
    'tags': 'tags',
    'tag_string': 'tags',
    'title': 'title',
    'commentary': 'commentary',
    **{k: k for k in Illust.__table__.columns.keys()},
}

ILLUST_POOLS_SUBQUERY = Illust.query.join(PoolIllust, Illust._pools).filter(Illust.id == PoolIllust.illust_id)\
    .with_entities(Illust.id)
POST_POOLS_SUBQUERY = Illust.query.join(IllustUrl, Illust.urls).join(Post, IllustUrl.post).join(PoolPost, Post._pools)\
    .filter(Post.id == PoolPost.post_id).with_entities(Illust.id)

POOL_SEARCH_KEYS = ['has_pools', 'has_post_pools', 'has_illust_pools']

# #### Load options

SHOW_HTML_OPTIONS = (
    selectinload(Illust.tags),
    selectinload(Illust.title),
    selectinload(Illust.commentary),
    selectinload(Illust.additional_commentaries),
    selectinload(Illust.artist).selectinload(Artist.boorus),
    selectinload(Illust.notations),
    selectinload(Illust._pools).selectinload(PoolIllust.pool),
)

SHOW_URLS_HTML_OPTIONS = (
    selectinload(IllustUrl.post).lazyload('*'),
)

INDEX_HTML_OPTIONS = (
    selectinload(Illust.tags),
    selectinload(Illust.urls).selectinload(IllustUrl.post).lazyload('*'),
)

JSON_OPTIONS = (
    selectinload(Illust.tags),
    selectinload(Illust.title),
    selectinload(Illust.commentary),
    selectinload(Illust.urls).lazyload('*'),
)


# #### Form

FORM_CONFIG = {
    'artist_id': {
        'name': 'Artist ID',
        'field': IntegerField,
        'kwargs': {
            'validators': [DataRequired()],
        },
    },
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
    'site_illust_id': {
        'name': 'Site Illust ID',
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
    'pages': {
        'field': IntegerField,
    },
    'score': {
        'field': IntegerField,
    },
    'tag_string': {
        'name': 'Tags',
        'field': TextAreaField,
        'kwargs': {
            'description': "Separated by whitespace.",
        },
    },
    'title': {
        'field': StringField,
    },
    'commentary': {
        'field': TextAreaField,
    },
    'active': {
        'field': BooleanField,
        'kwargs': {
            'default': True,
        },
    },
}


# ## FUNCTIONS

# #### Query functions

def pool_filter(query, search):
    pool_search_key = next((key for key in POOL_SEARCH_KEYS if key in search), None)
    if pool_search_key is not None and eval_bool_string(search[pool_search_key]) is not None:
        if pool_search_key == 'has_pools':
            subclause = or_(Illust.id.in_(POST_POOLS_SUBQUERY), Illust.id.in_(ILLUST_POOLS_SUBQUERY))
        elif pool_search_key == 'has_post_pools':
            subclause = Illust.id.in_(POST_POOLS_SUBQUERY)
        elif pool_search_key == 'has_illust_pools':
            subclause = Illust.id.in_(ILLUST_POOLS_SUBQUERY)
        if is_falsey(search[pool_search_key]):
            subclause = not_(subclause)
        query = query.filter(subclause)
    elif 'pool_id' in search and search['pool_id'].isdigit():
        query = query.unique_join(PoolIllust, Illust._pools).filter(PoolIllust.pool_id == int(search['pool_id']))
    return query


# #### Helper functions

def get_illust_form(**kwargs):
    return get_form('illust', FORM_CONFIG, **kwargs)


def uniqueness_check(dataparams, illust):
    site_name = dataparams.get('site_name', illust.site_name)
    site_illust_id = dataparams.get('site_illust_id', illust.site_illust_id)
    if site_name != illust.site_name or site_illust_id != illust.site_illust_id:
        return Illust.query.filter(Illust.site_value == site_name,
                                   Illust.site_illust_id == site_illust_id)\
                           .one_or_none()


def convert_data_params(dataparams):
    params = get_illust_form(**dataparams).data
    params['tags'] = parse_array_parameter(dataparams, 'tags', 'tag_string', r'\s')
    params['active'] = parse_bool_parameter(dataparams, 'active')
    params = nullify_blanks(params)
    return params


def convert_create_params(dataparams):
    createparams = convert_data_params(dataparams)
    set_default(createparams, 'pages', 1)
    set_default(createparams, 'score', 0)
    set_default(createparams, 'tags', [])
    if 'illust_urls' in dataparams:
        # Arrays of hashes are sent as a hash where each index is a key
        createparams['illust_urls'] = [v for v in dataparams['illust_urls'].values()]
        for url_data in createparams['illust_urls']:
            url_data['active'] = parse_bool_parameter(url_data, 'active')
    return createparams


def convert_update_params(dataparams):
    updateparams = convert_data_params(dataparams)
    updatelist = [VALUES_MAP[key] for key in dataparams if key in VALUES_MAP]
    updateparams = {k: v for (k, v) in updateparams.items() if k in updatelist}
    return updateparams


# #### Route helpers

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    negative_search = get_params_value(params, 'not', True)
    q = Illust.query
    q = search_filter(q, search, negative_search)
    q = pool_filter(q, search)
    if search.get('order') == 'site':
        q = q.order_by(Illust.site_illust_id.desc())
    else:
        q = default_order(q, search)
    return q


def create():
    dataparams = get_data_params(request, 'illust')
    createparams = convert_create_params(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    check_artist = Artist.find(createparams['artist_id'])
    if check_artist is None:
        return set_error(retdata, "artist #%s not found." % dataparams['artist_id'])
    errors = check_param_requirements(createparams, REQUIRED_PARAMS, 'create')
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    if createparams['site_name'] != check_artist.site_name:
        return set_error(retdata, "site_name parameter must match artist site_name value")
    check_illust = uniqueness_check(createparams, Illust())
    if check_illust is not None:
        retdata['item'] = check_illust.to_json()
        return set_error(retdata, "Illust already exists: %s" % check_illust.shortlink)
    illust = create_illust_from_parameters(createparams)
    retdata['item'] = illust.to_json()
    return retdata


def update(illust):
    dataparams = get_data_params(request, 'illust')
    updateparams = convert_update_params(dataparams)
    retdata = {'error': False, 'data': updateparams, 'params': dataparams}
    errors = check_param_requirements(updateparams, REQUIRED_PARAMS, 'update')
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    check_illust = uniqueness_check(updateparams, illust)
    if check_illust is not None:
        retdata['item'] = check_illust.to_json()
        return set_error(retdata, "Illust already exists: %s" % check_illust.shortlink)
    update_illust_from_parameters(illust, updateparams)
    retdata['item'] = illust.to_json()
    return retdata


def query_create():
    """Query source and create illust."""
    params = dict(url=request.values.get('url'))
    site_name = site_name_by_url(params['url'])
    createparams = {'site_name': site_name}
    retdata = {'error': False, 'params': params, 'createparams': createparams}
    if site_name == 'custom':
        return set_error(retdata, "Query create does not support URLs from custom domains.")
    source = source_by_site_name(site_name)
    createparams['site_illust_id'] = source.get_illust_id(params['url'])
    if createparams['site_illust_id'] is None:
        return set_error(retdata, "Unable to find site illust ID with URL.")
    check_illust = uniqueness_check(createparams, Illust())
    if check_illust is not None:
        retdata['item'] = check_illust.to_json()
        return set_error(retdata, "Illust already exists: %s" % check_illust.shortlink)
    retdata['data'] = source.get_illust_data(createparams['site_illust_id'])
    if not retdata['data']['active']:
        return set_error(retdata, "Illust post does not exist!")
    createparams.update(retdata['data'])
    site_artist_id = source.get_artist_id_by_illust_id(createparams['site_illust_id'])
    if site_artist_id is None:
        return set_error(retdata, "Unable to find site artist ID with URL.")
    artist = get_or_create_artist_from_source(site_artist_id, source)
    if artist is None:
        return set_error(retdata, "Unable to create artist with URL.")
    createparams['artist_id'] = artist.id
    illust = create_illust_from_parameters(createparams)
    retdata['item'] = illust.to_json()
    return retdata


def update_artist(illust):
    params = dict(artist_id=request.values.get('artist_id', type=int))
    retdata = {'error': False, 'params': params}
    if not isinstance(params['artist_id'], int):
        return set_error(retdata, "No artist ID included: %d" % str(params['artist_id']))
    artist = Artist.find(params['artist_id'])
    if artist is None:
        return set_error(retdata, "Artist ID is not valid: %d" % params['artist_id'])
    set_illust_artist(illust, artist)
    return retdata


def delete_title(illust):
    description_id = request.values.get('description_id', type=int)
    retdata = {'error': False, 'params': {'description_id': description_id}}
    if description_id is None:
        return set_error(retdata, "Description ID not set or a bad value.")
    retdata.update(illust_delete_title(illust, description_id))
    return retdata


def swap_title(illust):
    description_id = request.values.get('description_id', type=int)
    retdata = {'error': False, 'params': {'description_id': description_id}}
    if description_id is None:
        return set_error(retdata, "Description ID not set or a bad value.")
    retdata.update(illust_swap_title(illust, description_id))
    return retdata


def delete_commentary(illust):
    description_id = request.values.get('description_id', type=int)
    rel_type = request.values.get('relation')
    retdata = {'error': False, 'params': {'description_id': description_id, 'relation': rel_type}}
    if description_id is None:
        return set_error(retdata, "Description ID not set or a bad value.")
    if rel_type not in ('old', 'additional'):
        return set_error(retdata, "Invalid relation type set.")
    retdata.update(illust_delete_commentary(rel_type, illust, description_id))
    return retdata


def swap_commentary(illust):
    description_id = request.values.get('description_id', type=int)
    retdata = {'error': False, 'params': {'description_id': description_id}}
    if description_id is None:
        return set_error(retdata, "Description ID not set or a bad value.")
    retdata.update(illust_swap_commentary(illust, description_id))
    return retdata


# #### Route functions

# ###### SHOW

@bp.route('/illusts/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(Illust, id, options=JSON_OPTIONS)


@bp.route('/illusts/<int:id>', methods=['GET'])
def show_html(id):
    illust = get_or_abort(Illust, id, options=SHOW_HTML_OPTIONS)
    url_type = request.args.get('urls')
    illust_urls = illust.urls_paginate(page=get_page(request),
                                       per_page=get_limit(request, max_limit=8),
                                       options=SHOW_URLS_HTML_OPTIONS,
                                       url_type=url_type)
    return render_template("illusts/show.html", illust=illust, illust_urls=illust_urls)


# ###### INDEX

@bp.route('/illusts.json', methods=['GET'])
def index_json():
    q = index()
    q = q.options(JSON_OPTIONS)
    return index_json_response(q, request, distinct=True)


@bp.route('/illusts', methods=['GET'])
def index_html():
    q = index()
    q = q.options(INDEX_HTML_OPTIONS)
    page = paginate(q, request, distinct=True)
    return index_html_response(page, 'illust', 'illusts')


# ###### CREATE

@bp.route('/illusts/new', methods=['GET'])
def new_html():
    """HTML access point to create function."""
    form = get_illust_form(**request.args)
    artist = None
    if form.artist_id.data is not None:
        artist = Artist.find(form.artist_id.data)
        if artist is None:
            flash("illust #%d not a valid illust." % form.artist_id.data, 'error')
            form.artist_id.data = None
        else:
            hide_input(form, 'artist_id', artist.id)
            hide_input(form, 'site_name', artist.site_name)
    return render_template("illusts/new.html", form=form, artist=artist, illust=Illust())


@bp.route('/illusts', methods=['POST'])
def create_html():
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('illust.new_html', **results['data']))
    return redirect(url_for('illust.show_html', id=results['item']['id']))


@bp.route('/illusts.json', methods=['POST'])
def create_json():
    return create()


# ###### UPDATE

@bp.route('/illusts/<int:id>/edit', methods=['GET'])
def edit_html(id):
    """HTML access point to update function."""
    illust = get_or_abort(Illust, id)
    editparams = illust.basic_json()
    editparams['site_name'] = illust.site_name
    editparams['tag_string'] = '\r\n'.join(illust.tag_names)
    editparams['title'] = illust.title_body
    editparams['commentary'] = illust.commentary_body
    form = get_illust_form(**editparams)
    hide_input(form, 'artist_id', illust.artist_id)
    hide_input(form, 'site_name', illust.site_name)
    return render_template("illusts/edit.html", form=form, illust=illust)


@bp.route('/illusts/<int:id>', methods=['PUT'])
def update_html(id):
    illust = get_or_abort(Illust, id)
    results = update(illust)
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('illust.edit_html', id=illust.id))
    return redirect(url_for('illust.show_html', id=illust.id))


@bp.route('/illusts/<int:id>', methods=['PUT'])
def update_json(id):
    illust = get_or_error(Illust, id)
    if type(illust) is dict:
        return illust
    return update(illust)


# ###### DELETE

@bp.route('/illusts/<int:id>/archive', methods=['DELETE'])
def soft_delete_html(id):
    illust = get_or_abort(Illust, id)
    results = archive_illust_for_deletion(illust)
    if results['error']:
        flash(results['message'], 'error')
        if not results['is_deleted']:
            return redirect(request.referrer)
    if results['is_deleted']:
        flash("Illust deleted.")
    return redirect(url_for('archive.show_html', id=results['item']['id']))


@bp.route('/illusts/<int:id>', methods=['DELETE'])
def hard_delete_html(id):
    illust = get_or_abort(Illust, id)
    results = delete_illust(illust)
    if results['error']:
        flash(results['message'], 'error')
        if not results['is_deleted']:
            return redirect(request.referrer)
    if results['is_deleted']:
        flash("Illust deleted.")
    return redirect(url_for('illust.index_html'))


# ###### Misc

@bp.route('/illusts/<int:id>/archive', methods=['POST'])
def archive_illust_html(id):
    illust = get_or_abort(Illust, id)
    results = save_illust_to_archive(illust, None)
    if results['error']:
        flash(results['message'], 'error')
        return redirect(request.referrer)
    flash("Illust archived.")
    return redirect(url_for('archive.show_html', id=results['item']['id']))


@bp.route('/illusts/query_create', methods=['POST'])
def query_create_html():
    """Query source and create illust."""
    results = query_create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(request.referrer)
    flash('Illust created.')
    return redirect(url_for('illust.show_html', id=results['item']['id']))


@bp.route('/illusts/<int:id>/query_update', methods=['POST'])
def query_update_html(id):
    illust = get_or_abort(Illust, id)
    update_illust_from_source(illust)
    flash("Illust updated.")
    return redirect(url_for('illust.show_html', id=id))


@bp.route('/illusts/<int:id>/update_artist', methods=['POST'])
def update_artist_html(id):
    illust = get_or_abort(Illust, id)
    results = update_artist(illust)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash("Illust updated.")
    return redirect(url_for('illust.show_html', id=id))


@bp.route('/illusts/<int:id>/title', methods=['DELETE'])
def delete_title_html(id):
    illust = get_or_abort(Illust, id)
    results = delete_title(illust)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash('Commentary deleted.')
    return redirect(request.referrer)


@bp.route('/illusts/<int:id>/title', methods=['PUT'])
def swap_title_html(id):
    illust = get_or_abort(Illust, id)
    results = swap_title(illust)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash('Commentary swapped.')
    return redirect(request.referrer)


@bp.route('/illusts/<int:id>/commentary', methods=['DELETE'])
def delete_commentary_html(id):
    illust = get_or_abort(Illust, id)
    results = delete_commentary(illust)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash('Commentary deleted.')
    return redirect(request.referrer)


@bp.route('/illusts/<int:id>/commentary', methods=['PUT'])
def swap_commentary_html(id):
    illust = get_or_abort(Illust, id)
    results = swap_commentary(illust)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash('Commentary swapped.')
    return redirect(request.referrer)


@bp.route('/illusts/<int:id>/notate', methods=['POST'])
def create_commentary_from_source(id):
    illust = get_or_abort(Illust, id)
    source_url = request.values.get('url')
    if source_url is None:
        flash("Must include url parameter.", 'error')
        return redirect(request.referrer)
    source = get_post_source(source_url)
    if source is None:
        flash("Not a valid source.", 'error')
        return redirect(request.referrer)
    site_illust_id = source.get_illust_id(source_url)
    commentary = source.get_illust_commentary(site_illust_id)
    if commentary is None:
        flash("No commentaries found at source.", 'error')
        return redirect(request.referrer)
    commentary = "From " + (source.ILLUST_SHORTLINK % site_illust_id) + ":\n\n" + commentary
    results = illust_add_additional_commentary(illust, commentary)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash('Commentary added.')
    return redirect(url_for('illust.show_html', id=id))


@bp.route('/illusts/<int:id>/titles', methods=['GET'])
def titles_html(id):
    illust = get_or_abort(Illust, id)
    return render_template("illusts/titles.html", illust=illust)


@bp.route('/illusts/<int:id>/commentaries', methods=['GET'])
def commentaries_html(id):
    illust = get_or_abort(Illust, id)
    return render_template("illusts/commentaries.html", illust=illust)
