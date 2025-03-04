# APP/CONTROLLERS/ILLUST_URLS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, redirect, url_for, flash
from sqlalchemy.orm import selectinload
from wtforms import IntegerField, BooleanField, StringField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS
from ..models import Illust, IllustUrl
from ..logical.utility import set_error
from ..logical.sites import site_name_by_url
from ..logical.sources import source_by_site_name
from ..logical.sources.base_src import get_media_source
from ..logical.records.illust_rec import create_download_from_illust_url
from ..logical.database.illust_url_db import create_illust_url_from_parameters, update_illust_url_from_parameters
from .base_controller import get_params_value, process_request_values, show_json_response, index_json_response,\
    search_filter, default_order, paginate, get_data_params, get_form, get_or_abort, get_or_error,\
    nullify_blanks, check_param_requirements, hide_input, set_default, parse_bool_parameter, index_html_response


# ## GLOBAL VARIABLES

bp = Blueprint("illust_url", __name__)

CREATE_REQUIRED_PARAMS = ['illust_id', 'url']
VALUES_MAP = {
    'sample': 'sample',
    **{k: k for k in IllustUrl.__table__.columns.keys()},
}


# #### Load options

SHOW_HTML_OPTIONS = (
    selectinload(IllustUrl.post),
)

INDEX_HTML_OPTIONS = (
    selectinload(IllustUrl.post),
)


# #### Form

FORM_CONFIG = {
    'illust_id': {
        'name': 'Illust_id',
        'field': IntegerField,
        'kwargs': {
            'validators': [DataRequired()],
        },
    },
    'url': {
        'name': 'URL',
        'field': StringField,
    },
    'sample': {
        'field': StringField,
    },
    'width': {
        'field': IntegerField,
    },
    'height': {
        'field': IntegerField,
    },
    'order': {
        'field': IntegerField,
    },
    'active': {
        'field': BooleanField,
        'kwargs': {
            'default': True,
        },
    },
    'post_id': {
        'field': IntegerField,
    },
    'md5': {
        'field': StringField,
    },
}


# ## FUNCTIONS

# #### Helper functions

def get_illust_url_form(**kwargs):
    return get_form('illust_url', FORM_CONFIG, **kwargs)


def uniqueness_check(dataparams, illust_url):
    illust_id = dataparams.get('illust_id', illust_url.illust_id)
    site_name = dataparams.get('site_name', illust_url.site_name)
    url = dataparams.get('url', illust_url.url)
    if site_name != illust_url.site_name or url != illust_url.url:
        return IllustUrl.query.filter(IllustUrl.site_value == site_name,
                                      IllustUrl.illust_id == illust_id,
                                      IllustUrl.url == url)\
                              .one_or_none()


def convert_data_params(dataparams):
    params = get_illust_url_form(**dataparams).data
    params['active'] = parse_bool_parameter(dataparams, 'active')
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


def set_url_site(dataparams, source):
    dataparams['site_name'] = site_name_by_url(dataparams['url'])
    source = source_by_site_name(dataparams['site_name'])
    dataparams['url'] = source.partial_media_url(dataparams['url'])
    if dataparams.get('sample') is not None:
        dataparams['sample_site_name'] = site_name_by_url(dataparams['sample'])
        sample_source = source_by_site_name(dataparams['sample_site_name'])
        dataparams['sample_url'] = sample_source.partial_media_url(dataparams['sample'])


# #### Route helpers

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = IllustUrl.query
    q = search_filter(q, search)
    q = default_order(q, search)
    return q


def create():
    dataparams = get_data_params(request, 'illust_url')
    createparams = convert_create_params(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = check_param_requirements(createparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    illust = Illust.find(createparams['illust_id'])
    if illust is None:
        return set_error(retdata, "Illust #%d not found." % dataparams['illust_id'])
    source = get_media_source(createparams['url'])
    if source is None:
        return set_error(retdata, "URL is not a valid image URL from a recognized source.")
    set_url_site(createparams, source)
    check_illust_url = uniqueness_check(createparams, IllustUrl())
    if check_illust_url is not None:
        retdata['item'] = check_illust_url.to_json()
        return set_error(retdata, "Illust URL already exists: %s" % check_illust_url.shortlink)
    illust_url = create_illust_url_from_parameters(createparams)
    retdata['item'] = illust_url.to_json()
    return retdata


def update(illust_url):
    dataparams = get_data_params(request, 'illust_url')
    updateparams = convert_update_params(dataparams)
    retdata = {'error': False, 'data': updateparams, 'params': dataparams}
    if 'url' in updateparams:
        source = get_media_source(updateparams['url'])
        if source is None:
            return set_error(retdata, "URL is not a valid image URL from a recognized source.")
        set_url_site(updateparams, source)
        check_illust_url = uniqueness_check(updateparams, illust_url)
        if check_illust_url is not None:
            retdata['item'] = check_illust_url.to_json()
            return set_error(retdata, "Illust URL already exists: %s" % check_illust_url.shortlink)
    update_illust_url_from_parameters(illust_url, updateparams)
    retdata['item'] = illust_url.to_json()
    return retdata


# #### Route functions

# ###### SHOW

@bp.route('/illust_urls/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(IllustUrl, id)


@bp.route('/illust_urls/<int:id>', methods=['GET'])
def show_html(id):
    illust_url = get_or_abort(IllustUrl, id, options=SHOW_HTML_OPTIONS)
    return render_template("illust_urls/show.html", illust_url=illust_url)


# ###### INDEX

@bp.route('/illust_urls.json', methods=['GET'])
def index_json():
    q = index()
    return index_json_response(q, request)


@bp.route('/illust_urls', methods=['GET'])
def index_html():
    q = index()
    q = q.options(INDEX_HTML_OPTIONS)
    page = paginate(q, request)
    return index_html_response(page, 'illust_url', 'illust_urls')


# ###### CREATE

@bp.route('/illust_urls/new', methods=['GET'])
def new_html():
    """HTML access point to create function."""
    form = get_illust_url_form(**request.args)
    illust = None
    if form.illust_id.data is not None:
        illust = Illust.find(form.illust_id.data)
        if illust is None:
            flash("Illust #%d not a valid illust." % form.illust_id.data, 'error')
            form.illust_id.data = None
        else:
            hide_input(form, 'illust_id', illust.id)
    return render_template("illust_urls/new.html", form=form, illust_url=IllustUrl(), illust=illust)


@bp.route('/illust_urls', methods=['POST'])
def create_html():
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('illust_url.new_html', **results['data']))
    return redirect(url_for('illust.show_html', id=results['data']['illust_id']))


# ###### UPDATE

@bp.route('/illust_urls/<int:id>/edit', methods=['GET'])
def edit_html(id):
    """HTML access point to update function."""
    illust_url = get_or_abort(IllustUrl, id)
    editparams = illust_url.to_json()
    editparams['url'] = illust_url.full_url
    form = get_illust_url_form(**editparams)
    hide_input(form, 'illust_id', illust_url.illust_id)
    return render_template("illust_urls/edit.html", form=form, illust_url=illust_url)


@bp.route('/illust_urls/<int:id>', methods=['PUT'])
def update_html(id):
    illust_url = get_or_abort(IllustUrl, id)
    results = update(illust_url)
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('illust_url.edit_html', id=illust_url.id))
    return redirect(url_for('illust.show_html', id=illust_url.illust_id))


@bp.route('/illust_urls/<int:id>.json', methods=['PUT'])
def update_json(id):
    illust_url = get_or_error(IllustUrl, id)
    if type(illust_url) is dict:
        return illust_url
    return update(illust_url)


# ###### MISC

@bp.route('/illust_urls/<int:id>/download', methods=['POST'])
def download_html(id):
    illust_url = get_or_abort(IllustUrl, id)
    result = create_download_from_illust_url(illust_url)
    if result['error']:
        flash(result['message'], 'error')
    else:
        flash("%s downloaded" % illust_url.shortlink)
    return redirect(request.referrer)
