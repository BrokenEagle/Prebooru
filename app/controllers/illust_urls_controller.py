# APP\CONTROLLERS\ILLUST_URLS_CONTROLLER.PY

# ## PYTHON IMPORTS
from sqlalchemy.orm import selectinload
from flask import Blueprint, request, render_template, redirect, url_for, flash
from wtforms import IntegerField, BooleanField, StringField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS
from ..models import Illust, IllustUrl
from ..logical.sources.base import get_image_site_id, get_media_source
from ..database.illust_url_db import create_illust_url_from_parameters, update_illust_url_from_parameters
from .base_controller import get_params_value, process_request_values, show_json_response, index_json_response, search_filter, default_order, paginate,\
    get_data_params, CustomNameForm, get_or_abort, get_or_error, set_error, nullify_blanks, check_param_requirements, hide_input, set_default,\
    parse_bool_parameter


# ## GLOBAL VARIABLES

bp = Blueprint("illust_url", __name__)

CREATE_REQUIRED_PARAMS = ['illust_id', 'url']
VALUES_MAP = {
    **{k: k for k in IllustUrl.__table__.columns.keys()},
}


# #### Load options

SHOW_HTML_OPTIONS = (
    selectinload(IllustUrl.post),
)

INDEX_HTML_OPTIONS = (
    selectinload(IllustUrl.post),
)


# Forms

def get_illust_url_form(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class IllustUrlForm(CustomNameForm):
        illust_id = IntegerField('Illust ID', id='illust-url-illust_id', custom_name='illust_url[illust_id]', validators=[DataRequired()])
        url = StringField('URL', id='illust-url-url', custom_name='illust_url[url]', validators=[DataRequired()])
        width = IntegerField('Width', id='illust-url-width', custom_name='illust_url[width]')
        height = IntegerField('Height', id='illust-url-height', custom_name='illust_url[height]')
        order = IntegerField('Order', id='illust-url-order', custom_name='illust_url[order]')
        active = BooleanField('Active', id='illust-url-active', custom_name='illust_url[active]', default=True)
    return IllustUrlForm(**kwargs)


# ## FUNCTIONS

# #### Helper functions

def uniqueness_check(dataparams, illust_url):
    illust_id = dataparams['illust_id'] if 'illust_id' in dataparams else illust_url.illust_id
    site_id = dataparams['url'] if 'site_id' in dataparams else illust_url.site_id
    url = dataparams['url'] if 'url' in dataparams else illust_url.url
    if site_id != illust_url.site_id or url != illust_url.url:
        return IllustUrl.query.filter_by(illust_id=illust_id, site_id=site_id, url=url).first()


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
    dataparams['site_id'] = get_image_site_id(dataparams['url'])
    dataparams['url'] = source.partial_media_url(dataparams['url'])


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
    illust_urls = paginate(q, request)
    return render_template("illust_urls/index.html", illust_urls=illust_urls, illust_url=IllustUrl())


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
