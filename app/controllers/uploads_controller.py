# APP/CONTROLLERS/UPLOADS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, redirect, url_for, flash
from sqlalchemy.orm import selectinload
from wtforms import StringField, IntegerField, TextAreaField

# ## PACKAGE IMPORTS
from utility.data import eval_bool_string

# ## LOCAL IMPORTS
from .. import SCHEDULER
from ..models import Upload, UploadElement, IllustUrl, Illust, Post
from ..enum_imports import site_descriptor
from ..logical.utility import set_error
from ..logical.records.upload_rec import process_upload
from ..logical.records.media_file_rec import batch_get_or_create_media
from ..logical.database.upload_db import create_upload_from_parameters, set_upload_status
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_form, get_data_params, hide_input, parse_string_list,\
    nullify_blanks, set_default, get_or_abort, referrer_check, get_limit, get_page


# ## GLOBAL VARIABLES

bp = Blueprint("upload", __name__)


# #### Load options

SHOW_HTML_OPTIONS = (
    selectinload(Upload.elements).selectinload(UploadElement.illust_url).selectinload(IllustUrl.illust).options(
        selectinload(Illust._tags),
        selectinload(Illust.artist),
    ),
    selectinload(Upload.image_urls),
    selectinload(Upload.errors),
)

SHOW_ELEMENTS_HTML_OPTIONS = (
    selectinload(UploadElement.illust_url).selectinload(IllustUrl.post).lazyload('*'),
    selectinload(UploadElement.errors),
)

INDEX_HTML_OPTIONS = (
    selectinload(Upload.elements).selectinload(UploadElement.illust_url).selectinload(IllustUrl.post).selectinload(Post.media),
    selectinload(Upload.file_illust_url).selectinload(IllustUrl.post).selectinload(Post.media),
    selectinload(Upload.image_urls),
    selectinload(Upload.errors),
)

JSON_OPTIONS = (
    selectinload(Upload.elements).selectinload(UploadElement.illust_url).selectinload(IllustUrl.post),
    selectinload(Upload.image_urls),
    selectinload(Upload.errors),
)


# #### Form

FORM_CONFIG = {
    'illust_url_id': {
        'name': 'Illust URL ID',
        'field': IntegerField,
    },
    'media_filepath': {
        'field': StringField,
    },
    'sample_filepath': {
        'field': StringField,
    },
    'request_url': {
        'name': 'Request URL',
        'field': StringField,
    },
    'image_url_string': {
        'name': 'Image URLs',
        'field': TextAreaField,
        'kwargs': {
            'description': "Separated by carriage returns.",
        },
    },
}


# ## FUNCTIONS

# #### Helper functions

def get_upload_form(**kwargs):
    return get_form('upload', FORM_CONFIG, **kwargs)


def uniqueness_check(createparams):
    q = Upload.query
    if createparams['illust_url_id']:
        q = q.filter(Upload.illust_url_id == createparams['illust_url_id'])
    elif createparams['request_url']:
        q = q.filter(Upload.request_url == createparams['request_url'])
    return q.first()


def convert_data_params(dataparams):
    params = get_upload_form(**dataparams).data
    if 'image_urls' in dataparams:
        params['image_urls'] = dataparams['image_urls']
    elif 'image_url_string' in dataparams:
        dataparams['image_urls'] = params['image_urls'] = parse_string_list(dataparams, 'image_url_string', r'\r?\n')
    params = nullify_blanks(params)
    return params


def convert_create_params(dataparams):
    createparams = convert_data_params(dataparams)
    set_default(createparams, 'image_urls', [])
    if createparams['illust_url_id']:
        createparams['request_url'] = None
        createparams['image_urls'] = []
    elif createparams['request_url']:
        createparams['request_url'] = createparams['request_url'].split('#')[0]
        createparams['illust_url_id'] = None
    return createparams


def check_create_params(dataparams, request_url_only):
    if request_url_only and dataparams['request_url'] is None:
        return ["Must include the request URL."]
    if dataparams['illust_url_id'] is None and dataparams['request_url'] is None:
        return ["Must include the illust URL ID or the request URL."]
    if dataparams['illust_url_id'] and not dataparams['media_filepath']:
        return ["Must include the media filepath for file uploads."]
    return []


# #### Route auxiliary functions

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = Upload.query
    q = search_filter(q, search)
    q = default_order(q, search)
    return q


def create(get_request=False):
    force_download = request.values.get('force', type=eval_bool_string)
    image_urls_only = request.values.get('image_urls_only', type=eval_bool_string)
    request_url_only = request.values.get('request_url_only', type=eval_bool_string) or get_request
    dataparams = get_data_params(request, 'upload')
    createparams = convert_create_params(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = check_create_params(createparams, request_url_only)
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    if image_urls_only and len(createparams['image_urls']) == 0:
        return set_error(retdata, "No image URLs set!")
    if not force_download:
        check_upload = uniqueness_check(createparams)
        if check_upload is not None:
            retdata['item'] = check_upload.to_json()
            return set_error(retdata, "Upload already exists: upload #%d" % check_upload.id)
    if createparams['request_url']:
        site = site_descriptor.get_site_from_url(createparams['request_url'])
        if site.name == 'custom':
            msg = "Upload source currently not handled for request url: %s" % createparams['request_url']
            return set_error(retdata, msg)
        source = site.source
        createparams['image_urls'] = [url for url in createparams['image_urls'] if source.is_image_url(url)]
        createparams['type'] = 'post'
    elif createparams['illust_url_id']:
        createparams['type'] = 'file'
    upload = create_upload_from_parameters(createparams)
    retdata['item'] = upload.to_json()
    SCHEDULER.add_job("process_upload-%d" % retdata['item']['id'], process_upload, args=(retdata['item']['id'],))
    return retdata


def upload_select():
    dataparams = get_data_params(request, 'upload')
    selectparams = convert_data_params(dataparams)
    retdata = {'error': False, 'data': selectparams, 'params': dataparams}
    if 'request_url' not in selectparams:
        return set_error(retdata, "Request URL not specified.")
    selectparams['request_url'] = selectparams['request_url'].split('#')[0]
    errors = check_create_params(selectparams, True)
    if len(errors):
        return set_error(retdata, '\n'.join(errors))
    site = site_descriptor.get_site_from_url(selectparams['request_url'])
    if site.name == 'custom':
        msg = "Upload source currently not handled for request url: %s" % selectparams['request_url']
        return set_error(retdata, msg)
    source = site.source
    site_illust_id = source.get_illust_id(selectparams['request_url'])
    illust_data = source.get_illust_data(site_illust_id)
    media_batches = []
    for url_data in illust_data['illust_urls']:
        url_data['full_url'] = full_url = source.normalized_image_url(url_data['url'])
        url_data['preview_url'] = source.small_image_url(full_url)
        media_batches.append((url_data['preview_url'], source))
    media_files = batch_get_or_create_media(media_batches)
    for (i, media) in enumerate(media_files):
        url_data = illust_data['illust_urls'][i]
        if isinstance(media, str):
            flash(media, 'error')
            url_data['media_file'] = None
        else:
            url_data['media_file'] = media
    retdata['item'] = illust_data['illust_urls']
    return retdata


# #### Route functions

# ###### SHOW

@bp.route('/uploads/<int:id>.json')
def show_json(id):
    return show_json_response(Upload, id, options=JSON_OPTIONS)


@bp.route('/uploads/<int:id>')
def show_html(id):
    upload = get_or_abort(Upload, id, options=SHOW_HTML_OPTIONS)
    elements = upload.elements_paginate(page=get_page(request),
                                        per_page=get_limit(request, max_limit=8),
                                        options=SHOW_ELEMENTS_HTML_OPTIONS)
    return render_template("uploads/show.html", upload=upload, elements=elements)


# ###### INDEX

@bp.route('/uploads.json', methods=['GET'])
def index_json():
    q = index()
    q = q.options(JSON_OPTIONS)
    return index_json_response(q, request)


@bp.route('/uploads', methods=['GET'])
def index_html():
    from utility.uprint import print_info
    q = index()
    q = q.options(INDEX_HTML_OPTIONS)
    uploads = paginate(q, request)
    print_info("Before page render")
    return render_template("uploads/index.html", uploads=uploads, upload=Upload())


# ###### CREATE

@bp.route('/uploads/new', methods=['GET'])
def new_html():
    """HTML access point to create function."""
    illust_url = None
    form = get_upload_form(**request.args)
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
            hide_input(form, 'illust_url_id', illust_url.id)
            hide_input(form, 'request_url')
            hide_input(form, 'image_url_string')
    return render_template("uploads/new.html", form=form, upload=Upload(), illust_url=illust_url)


@bp.route('/uploads', methods=['POST'])
def create_html():
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        data = {'noprocess': True, 'upload[request_url]': results['data']['request_url']}
        if referrer_check('upload.upload_all_html', request):
            return redirect(url_for('upload.upload_all_html', **data))
        if referrer_check('upload.upload_select_html', request):
            return redirect(url_for('upload.upload_select_html', **data))
        return redirect(url_for('upload.new_html', **results['data']))
    return redirect(url_for('upload.show_html', id=results['item']['id']))


@bp.route('/uploads.json', methods=['POST'])
def create_json():
    return create()


# ###### MISC

@bp.route('/uploads/all', methods=['GET'])
def upload_all_html():
    show_form = request.args.get('show_form', type=eval_bool_string)
    if show_form:
        return render_template("uploads/all.html", form=get_upload_form(), upload=Upload())
    results = create(True)
    if results['error']:
        flash(results['message'], 'error')
        form = get_upload_form(**results['data'])
        return render_template("uploads/all.html", form=form, upload=Upload())
    return redirect(url_for('upload.show_html', id=results['item']['id']))


@bp.route('/uploads/select', methods=['GET'])
def upload_select_html():
    show_form = request.args.get('show_form', type=eval_bool_string)
    if show_form:
        return render_template("uploads/select.html", illust_urls=None, form=get_upload_form(), upload=Upload())
    results = upload_select()
    form = get_upload_form(request_url=results['data']['request_url'])
    if results['error']:
        flash(results['message'], 'error')
        return render_template("uploads/select.html", illust_urls=None, form=form, upload=Upload())
    return render_template("uploads/select.html", form=form, illust_urls=results['item'], upload=Upload())


@bp.route('/uploads/<int:id>/check', methods=['POST'])
def upload_check_html(id):
    get_or_abort(Upload, id)
    SCHEDULER.add_job("process_upload-%d" % id, process_upload, args=(id,))
    return redirect(request.referrer)


@bp.route('/uploads/<int:id>/resubmit', methods=['POST'])
def resubmit_html(id):
    upload = get_or_abort(Upload, id)
    set_upload_status(upload, 'pending')
    SCHEDULER.add_job("process_upload-%d" % id, process_upload, args=(id,))
    return redirect(request.referrer)
