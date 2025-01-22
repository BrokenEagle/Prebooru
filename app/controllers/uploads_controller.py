# APP/CONTROLLERS/UPLOADS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, redirect, url_for, flash
from sqlalchemy.orm import selectinload
from wtforms import StringField, IntegerField

# ## PACKAGE IMPORTS
from utility.data import eval_bool_string

# ## LOCAL IMPORTS
from .. import SCHEDULER
from ..models import Upload, IllustUrl
from ..logical.utility import set_error
from ..logical.records.upload_rec import process_upload
from ..logical.database.upload_db import create_upload_from_parameters, update_upload_from_parameters
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_form, get_data_params, hide_input,\
    nullify_blanks, get_or_abort, index_html_response


# ## GLOBAL VARIABLES

bp = Blueprint("upload", __name__)

RECHECK_UPLOADS = None
INIT = False

# #### Load options

SHOW_HTML_OPTIONS = (
    selectinload(Upload.illust_url).selectinload(IllustUrl.post),
    selectinload(Upload.errors),
)

INDEX_HTML_OPTIONS = (
    selectinload(Upload.illust_url).selectinload(IllustUrl.post),
    selectinload(Upload.errors),
)

JSON_OPTIONS = (
    selectinload(Upload.illust_url).selectinload(IllustUrl.post),
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
}


# ## FUNCTIONS

# #### Helper functions

def get_upload_form(**kwargs):
    return get_form('upload', FORM_CONFIG, **kwargs)


def uniqueness_check(createparams):
    return Upload.query.filter(Upload.illust_url_id == createparams['illust_url_id']).first()


def convert_data_params(dataparams):
    params = get_upload_form(**dataparams).data
    params = nullify_blanks(params)
    return params


def convert_create_params(dataparams):
    return convert_data_params(dataparams)


def check_create_params(dataparams):
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
    global RECHECK_UPLOADS
    force_download = request.values.get('force', type=eval_bool_string)
    dataparams = get_data_params(request, 'upload')
    createparams = convert_create_params(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = check_create_params(createparams)
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    if not force_download:
        check_upload = uniqueness_check(createparams)
        if check_upload is not None:
            retdata['item'] = check_upload.to_json()
            return set_error(retdata, "Upload already exists.")
    upload = create_upload_from_parameters(createparams)
    retdata['item'] = upload.to_json()
    SCHEDULER.add_job("process_upload-%d" % upload.id, process_upload, args=(upload.id,))
    return retdata


# #### Route functions

# ###### SHOW

@bp.route('/uploads/<int:id>.json')
def show_json(id):
    return show_json_response(Upload, id, options=JSON_OPTIONS)


@bp.route('/uploads/<int:id>')
def show_html(id):
    upload = get_or_abort(Upload, id, options=SHOW_HTML_OPTIONS)
    return render_template("uploads/show.html", upload=upload)


# ###### INDEX

@bp.route('/uploads.json', methods=['GET'])
def index_json():
    q = index()
    q = q.options(JSON_OPTIONS)
    return index_json_response(q, request)


@bp.route('/uploads', methods=['GET'])
def index_html():
    q = index()
    q = q.options(INDEX_HTML_OPTIONS)
    page = paginate(q, request)
    return index_html_response(page, 'upload', 'uploads')


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
    return render_template("uploads/new.html", form=form, upload=Upload(), illust_url=illust_url)


@bp.route('/uploads', methods=['POST'])
def create_html():
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('upload.new_html', **results['data']))
    return redirect(url_for('upload.show_html', id=results['item']['id']))


@bp.route('/uploads.json', methods=['POST'])
def create_json():
    return create()


# ###### MISC

@bp.route('/uploads/<int:id>/check', methods=['POST'])
def upload_check_html(id):
    get_or_abort(Upload, id)
    SCHEDULER.add_job("process_upload-%d" % id, process_upload, args=(id,))
    return redirect(request.referrer)


@bp.route('/uploads/<int:id>/resubmit', methods=['POST'])
def resubmit_html(id):
    upload = get_or_abort(Upload, id)
    update_upload_from_parameters(upload, {'status_name': 'pending'})
    SCHEDULER.add_job("process_upload-%d" % id, process_upload, args=(id,))
    return redirect(request.referrer)
