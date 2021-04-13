# APP\CONTROLLERS\UPLOADS.PY

# ## PYTHON IMPORTS
from sqlalchemy.orm import selectinload
from flask import Blueprint, request, render_template, redirect, url_for, flash
from wtforms import StringField, IntegerField, TextAreaField

# ## LOCAL IMPORTS
from ..logical.utility import EvalBoolString
from ..models import Upload, Post, IllustUrl, Illust
from ..sources.base_source import GetPostSource, GetPreviewUrl
from ..sources.local_source import WorkerCheckUploads
from ..database.upload_db import CreateUploadFromParameters
from ..database.cache_db import GetMediaData
from .base_controller import ShowJson, IndexJson, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate, DefaultOrder, CustomNameForm, GetDataParams,\
    HideInput, ParseStringList, NullifyBlanks, SetDefault, SetError, GetOrAbort, ReferrerCheck


# ## GLOBAL VARIABLES


bp = Blueprint("upload", __name__)


# #### Load options

SHOW_HTML_OPTIONS = (
    selectinload(Upload.posts).selectinload(Post.illust_urls).selectinload(IllustUrl.illust).options(
        selectinload(Illust.tags),
        selectinload(Illust.artist),
    ),
    selectinload(Upload.image_urls),
    selectinload(Upload.errors),
)

INDEX_HTML_OPTIONS = (
    selectinload(Upload.posts),
    selectinload(Upload.image_urls),
    selectinload(Upload.errors),
)

JSON_OPTIONS = (
    selectinload(Upload.posts),
    selectinload(Upload.image_urls),
    selectinload(Upload.errors),
)


# #### Forms

def GetUploadForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class UploadForm(CustomNameForm):
        illust_url_id = IntegerField('Illust URL ID', id='upload-illust-url-id', custom_name='upload[illust_url_id]')
        media_filepath = StringField('Media filepath', id='upload-media-filepath', custom_name='upload[media_filepath]')
        sample_filepath = StringField('Sample filepath', id='upload-sample-filepath', custom_name='upload[sample_filepath]')
        request_url = StringField('Request URL', id='upload-request-url', custom_name='upload[request_url]')
        image_url_string = TextAreaField('Image URLs', id='upload-image-url-string', custom_name='upload[image_url_string]', description="Separated by carriage returns.")
    return UploadForm(**kwargs)


# ## FUNCTIONS

# #### Helper functions

def UniquenessCheck(createparams):
    q = Upload.query
    if createparams['illust_url_id']:
        q = q.filter(Upload.illust_url_id == createparams['illust_url_id'])
    elif createparams['request_url']:
        q = q.filter(Upload.request_url == createparams['request_url'])
    return q.first()


def ConvertDataParams(dataparams):
    params = GetUploadForm(**dataparams).data
    if 'image_urls' in dataparams:
        params['image_urls'] = dataparams['image_urls']
    elif 'image_url_string' in dataparams:
        dataparams['image_urls'] = params['image_urls'] = ParseStringList(dataparams, 'image_url_string', r'\r?\n')
    params = NullifyBlanks(params)
    return params


def ConvertCreateParams(dataparams):
    createparams = ConvertDataParams(dataparams)
    SetDefault(createparams, 'image_urls', [])
    if createparams['illust_url_id']:
        createparams['request_url'] = None
        createparams['image_urls'] = []
    elif createparams['request_url']:
        createparams['illust_url_id'] = None
    return createparams


def CheckCreateParams(dataparams, request_url_only):
    if request_url_only and dataparams['request_url'] is None:
        return ["Must include the request URL."]
    if dataparams['illust_url_id'] is None and dataparams['request_url'] is None:
        return ["Must include the illust URL ID or the request URL."]
    if dataparams['illust_url_id'] and not dataparams['media_filepath']:
        return ["Must include the media filepath for file uploads."]
    return []


# #### Route auxiliary functions

def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    q = Upload.query
    q = SearchFilter(q, search)
    q = DefaultOrder(q, search)
    return q


def create(get_request=False):
    force_download = request.values.get('force', type=EvalBoolString)
    image_urls_only = request.values.get('image_urls_only', type=EvalBoolString)
    request_url_only = request.values.get('request_url_only', type=EvalBoolString) or get_request
    dataparams = GetDataParams(request, 'upload')
    createparams = ConvertCreateParams(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = CheckCreateParams(createparams, request_url_only)
    if len(errors) > 0:
        return SetError(retdata, '\n'.join(errors))
    if image_urls_only and len(createparams['image_urls']) == 0:
        return SetError(retdata, "No image URLs set!")
    if not force_download:
        check_upload = UniquenessCheck(createparams)
        if check_upload is not None:
            retdata['item'] = check_upload.to_json()
            return SetError(retdata, "Upload already exists: upload #%d" % check_upload.id)
    if createparams['request_url']:
        source = GetPostSource(createparams['request_url'])
        if source is None:
            return SetError(retdata, "Upload source currently not handled for request url: %s" % createparams['request_url'])
        createparams['image_urls'] = [url for url in createparams['image_urls'] if source.IsImageUrl(url)]
        createparams['type'] = 'post'
    elif createparams['illust_url_id']:
        createparams['type'] = 'file'
    upload = CreateUploadFromParameters(createparams)
    retdata['item'] = upload.to_json()
    return retdata


def upload_select():
    dataparams = GetDataParams(request, 'upload')
    selectparams = ConvertDataParams(dataparams)
    retdata = {'error': False, 'data': selectparams, 'params': dataparams}
    errors = CheckCreateParams(selectparams, True)
    if len(errors):
        return SetError(retdata, '\n'.join(errors))
    source = GetPostSource(selectparams['request_url'])
    if source is None:
        return SetError(retdata, "Upload source currently not handled for request url: %s" % selectparams['request_url'])
    site_illust_id = source.GetIllustId(selectparams['request_url'])
    illust_data = source.GetIllustData(site_illust_id)
    for url_data in illust_data['illust_urls']:
        full_url = GetPreviewUrl(url_data['url'], url_data['site_id'])
        url_data['full_url'] = full_url
        url_data['preview_url'] = source.SmallImageUrl(full_url)
        media = GetMediaData(url_data['preview_url'], source)
        if type(media) is str:
            flash(media, 'error')
            url_data['media_url'] = None
        else:
            url_data['media_url'] = media.file_url
    retdata['item'] = illust_data['illust_urls']
    return retdata


# #### Route functions

# ###### SHOW

@bp.route('/uploads/<int:id>.json')
def show_json(id):
    return ShowJson(Upload, id, options=JSON_OPTIONS)


@bp.route('/uploads/<int:id>')
def show_html(id):
    upload = GetOrAbort(Upload, id, options=SHOW_HTML_OPTIONS)
    return render_template("uploads/show.html", upload=upload)


# ###### INDEX

@bp.route('/uploads.json', methods=['GET'])
def index_json():
    q = index()
    q = q.options(JSON_OPTIONS)
    return IndexJson(q, request)


@bp.route('/uploads', methods=['GET'])
def index_html():
    q = index()
    q = q.options(INDEX_HTML_OPTIONS)
    uploads = Paginate(q, request)
    return render_template("uploads/index.html", uploads=uploads, upload=Upload())


# ###### CREATE

@bp.route('/uploads/new', methods=['GET'])
def new_html():
    """HTML access point to create function."""
    illust_url = None
    form = GetUploadForm(**request.args)
    if form.illust_url_id.data is not None:
        illust_url = IllustUrl.find(form.illust_url_id.data)
        if illust_url is None:
            flash("Illust URL #%d does not exist." % form.illust_url_id.data, 'error')
            form.illust_url_id.data = None
        elif illust_url.post is not None:
            flash("Illust URL #%d already uploaded on post #%d." % (illust_url.id, illust_url.post.id), 'error')
            form.illust_url_id.data = None
            illust_url = None
        else:
            HideInput(form, 'illust_url_id', illust_url.id)
            HideInput(form, 'request_url')
            HideInput(form, 'image_url_string')
    return render_template("uploads/new.html", form=form, upload=Upload(), illust_url=illust_url)


@bp.route('/uploads', methods=['POST'])
def create_html():
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        data = {'noprocess': True, 'upload[request_url]': results['data']['request_url']}
        if ReferrerCheck('upload.upload_all_html', request):
            return redirect(url_for('upload.upload_all_html', **data))
        if ReferrerCheck('upload.upload_select_html', request):
            return redirect(url_for('upload.upload_select_html', **data))
        return redirect(url_for('upload.new_html', **results['data']))
    worker_results = WorkerCheckUploads()
    if worker_results['error']:
        flash(worker_results['message'], 'error')
    return redirect(url_for('upload.show_html', id=results['item']['id']))


@bp.route('/uploads.json', methods=['POST'])
def create_json():
    results = create()
    if results['error']:
        return results
    results['worker'] = WorkerCheckUploads()
    return results


# ###### MISC

@bp.route('/uploads/all', methods=['GET'])
def upload_all_html():
    show_form = request.args.get('show_form', type=EvalBoolString)
    if show_form:
        return render_template("uploads/all.html", form=GetUploadForm(), upload=Upload())
    results = create(True)
    if results['error']:
        flash(results['message'], 'error')
        form = GetUploadForm(**results['data'])
        return render_template("uploads/all.html", form=form, upload=Upload())
    worker_results = WorkerCheckUploads()
    if worker_results['error']:
        flash(worker_results['message'], 'error')
    return redirect(url_for('upload.show_html', id=results['item']['id']))


@bp.route('/uploads/select', methods=['GET'])
def upload_select_html():
    show_form = request.args.get('show_form', type=EvalBoolString)
    if show_form:
        return render_template("uploads/select.html", illust_urls=None, form=GetUploadForm(), upload=Upload())
    results = upload_select()
    form = GetUploadForm(request_url=results['data']['request_url'])
    if results['error']:
        flash(results['message'], 'error')
        return render_template("uploads/select.html", illust_urls=None, form=form, upload=Upload())
    return render_template("uploads/select.html", form=form, illust_urls=results['item'], upload=Upload())


@bp.route('/uploads/check', methods=['GET'])
def upload_check_html():
    results = WorkerCheckUploads()
    if results['error']:
        flash(results['message'], 'error')
    return redirect(request.referrer)
