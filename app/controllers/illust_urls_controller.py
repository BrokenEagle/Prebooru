# APP\CONTROLLERS\ILLUST_URLS_CONTROLLER.PY

# ## PYTHON IMPORTS
from sqlalchemy.orm import selectinload
from flask import Blueprint, request, render_template, redirect, url_for, flash
from wtforms import IntegerField, BooleanField, StringField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS
from ..models import Illust, IllustUrl
from ..sources.base_source import GetImageSiteId, GetImageSource
from ..database.illust_url_db import CreateIllustUrlFromParameters, UpdateIllustUrlFromParameters
from .base_controller import GetParamsValue, ProcessRequestValues, ShowJson, IndexJson, SearchFilter, DefaultOrder, Paginate,\
    GetDataParams, CustomNameForm, GetOrAbort, GetOrError, SetError, NullifyBlanks, CheckParamRequirements, HideInput, SetDefault,\
    ParseBoolParameter


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

def GetIllustUrlForm(**kwargs):
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

def UniquenessCheck(dataparams, illust_url):
    illust_id = dataparams['illust_id'] if 'illust_id' in dataparams else illust_url.illust_id
    site_id = dataparams['url'] if 'site_id' in dataparams else illust_url.site_id
    url = dataparams['url'] if 'url' in dataparams else illust_url.url
    if site_id != illust_url.site_id or url != illust_url.url:
        return IllustUrl.query.filter_by(illust_id=illust_id, site_id=site_id, url=url).first()


def ConvertDataParams(dataparams):
    params = GetIllustUrlForm(**dataparams).data
    params['active'] = ParseBoolParameter(dataparams, 'active')
    params = NullifyBlanks(params)
    return params


def ConvertCreateParams(dataparams):
    createparams = ConvertDataParams(dataparams)
    SetDefault(createparams, 'active', True)
    return createparams


def ConvertUpdateParams(dataparams):
    updateparams = ConvertDataParams(dataparams)
    updatelist = [VALUES_MAP[key] for key in dataparams if key in VALUES_MAP]
    updateparams = {k: v for (k, v) in updateparams.items() if k in updatelist}
    return updateparams


def SetURLSite(dataparams, source):
    dataparams['site_id'] = GetImageSiteId(dataparams['url'])
    dataparams['url'] = source.PartialMediaUrl(dataparams['url'])


# #### Route helpers

def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    q = IllustUrl.query
    q = SearchFilter(q, search)
    q = DefaultOrder(q, search)
    return q


def create():
    dataparams = GetDataParams(request, 'illust_url')
    createparams = ConvertCreateParams(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = CheckParamRequirements(createparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return SetError(retdata, '\n'.join(errors))
    illust = Illust.find(createparams['illust_id'])
    if illust is None:
        return SetError(retdata, "Illust #%d not found." % dataparams['illust_id'])
    source = GetImageSource(createparams['url'])
    if source is None:
        return SetError(retdata, "URL is not a valid image URL from a recognized source.")
    SetURLSite(createparams, source)
    check_illust_url = UniquenessCheck(createparams, IllustUrl())
    if check_illust_url is not None:
        retdata['item'] = check_illust_url.to_json()
        return SetError(retdata, "Illust URL already exists: %s" % check_illust_url.shortlink)
    illust_url = CreateIllustUrlFromParameters(createparams)
    retdata['item'] = illust_url.to_json()
    return retdata


def update(illust_url):
    dataparams = GetDataParams(request, 'illust_url')
    updateparams = ConvertUpdateParams(dataparams)
    retdata = {'error': False, 'data': updateparams, 'params': dataparams}
    if 'url' in updateparams:
        source = GetImageSource(updateparams['url'])
        if source is None:
            return SetError(retdata, "URL is not a valid image URL from a recognized source.")
        SetURLSite(updateparams, source)
        check_illust_url = UniquenessCheck(updateparams, illust_url)
        if check_illust_url is not None:
            retdata['item'] = check_illust_url.to_json()
            return SetError(retdata, "Illust URL already exists: %s" % check_illust_url.shortlink)
    UpdateIllustUrlFromParameters(illust_url, updateparams)
    retdata['item'] = illust_url.to_json()
    return retdata


# #### Route functions

# ###### SHOW

@bp.route('/illust_urls/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(IllustUrl, id)


@bp.route('/illust_urls/<int:id>', methods=['GET'])
def show_html(id):
    illust_url = GetOrAbort(IllustUrl, id, options=SHOW_HTML_OPTIONS)
    return render_template("illust_urls/show.html", illust_url=illust_url)


# ###### INDEX

@bp.route('/illust_urls.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/illust_urls', methods=['GET'])
def index_html():
    q = index()
    q = q.options(INDEX_HTML_OPTIONS)
    illust_urls = Paginate(q, request)
    return render_template("illust_urls/index.html", illust_urls=illust_urls, illust_url=IllustUrl())


# ###### CREATE

@bp.route('/illust_urls/new', methods=['GET'])
def new_html():
    """HTML access point to create function."""
    form = GetIllustUrlForm(**request.args)
    illust = None
    if form.illust_id.data is not None:
        illust = Illust.find(form.illust_id.data)
        if illust is None:
            flash("Illust #%d not a valid illust." % form.illust_id.data, 'error')
            form.illust_id.data = None
        else:
            HideInput(form, 'illust_id', illust.id)
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
    illust_url = GetOrAbort(IllustUrl, id)
    editparams = illust_url.to_json()
    editparams['url'] = illust_url.full_url
    form = GetIllustUrlForm(**editparams)
    HideInput(form, 'illust_id', illust_url.illust_id)
    return render_template("illust_urls/edit.html", form=form, illust_url=illust_url)


@bp.route('/illust_urls/<int:id>', methods=['PUT'])
def update_html(id):
    illust_url = GetOrAbort(IllustUrl, id)
    results = update(illust_url)
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('illust_url.edit_html', id=illust_url.id))
    return redirect(url_for('illust.show_html', id=illust_url.illust_id))


@bp.route('/illust_urls/<int:id>.json', methods=['PUT'])
def update_json(id):
    illust_url = GetOrError(IllustUrl, id)
    if type(illust_url) is dict:
        return illust_url
    return update(illust_url)
