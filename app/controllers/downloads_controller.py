# APP/CONTROLLERS/DOWNLOADS_CONTROLLER.PY

# ## PYTHON IMPORTS
import threading
import urllib.parse

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, redirect, url_for, flash
from sqlalchemy.orm import selectinload
from wtforms import StringField, TextAreaField

# ## PACKAGE IMPORTS
from utility import RepeatTimer
from utility.time import minutes_ago
from utility.data import eval_bool_string
from utility.uprint import print_warning

# ## LOCAL IMPORTS
from .. import SCHEDULER, SESSION, MAIN_PROCESS
from ..models import Download, DownloadElement, IllustUrl, Illust
from ..logical.utility import set_error
from ..logical.sites import site_name_by_url
from ..logical.sources import source_by_site_name
from ..logical.records.download_rec import process_download
from ..logical.records.media_file_rec import batch_get_or_create_media
from ..logical.database.download_db import create_download_from_parameters, update_download_from_parameters,\
    get_pending_downloads
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_form, get_data_params, parse_string_list,\
    nullify_blanks, set_default, get_or_abort, referrer_check, get_limit, get_page, index_html_response


# ## GLOBAL VARIABLES

bp = Blueprint("download", __name__)

RECHECK_DOWNLOADS = None

# #### Load options

SHOW_HTML_OPTIONS = (
    selectinload(Download.elements).selectinload(DownloadElement.illust_url).selectinload(IllustUrl.illust).options(
        selectinload(Illust.tags),
        selectinload(Illust.artist),
    ),
    selectinload(Download.image_urls),
    selectinload(Download.errors),
)

SHOW_ELEMENTS_HTML_OPTIONS = (
    selectinload(DownloadElement.illust_url).selectinload(IllustUrl.post).lazyload('*'),
    selectinload(DownloadElement.errors),
)

INDEX_HTML_OPTIONS = (
    selectinload(Download.elements).selectinload(DownloadElement.illust_url).selectinload(IllustUrl.post),
    selectinload(Download.image_urls),
    selectinload(Download.errors),
)

JSON_OPTIONS = (
    selectinload(Download.elements).selectinload(DownloadElement.illust_url).selectinload(IllustUrl.post),
    selectinload(Download.image_urls),
    selectinload(Download.errors),
)


# #### Form

FORM_CONFIG = {
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

def get_download_form(**kwargs):
    return get_form('download', FORM_CONFIG, **kwargs)


def uniqueness_check(createparams):
    return Download.query.filter(Download.request_url == createparams['request_url']).first()


def convert_data_params(dataparams):
    params = get_download_form(**dataparams).data
    if 'image_urls' in dataparams:
        params['image_urls'] = dataparams['image_urls']
    elif 'image_url_string' in dataparams:
        dataparams['image_urls'] = params['image_urls'] = parse_string_list(dataparams, 'image_url_string', r'\r?\n')
    params = nullify_blanks(params)
    return params


def convert_create_params(dataparams):
    createparams = convert_data_params(dataparams)
    set_default(createparams, 'image_urls', [])
    createparams['request_url'] = createparams['request_url'].split('#')[0]
    return createparams


def check_create_params(dataparams):
    if dataparams['request_url'] is None:
        return ["Must include the request URL."]
    return []


def validate_request_url(request_url):
    parse = urllib.parse.urlparse(request_url)
    if not all([parse.scheme, parse.netloc]):
        return "Request url is not a valid URL"
    site_name = site_name_by_url(request_url)
    if site_name == 'custom':
        return "%s not a valid domain for request URLs" % parse.netloc
    source = source_by_site_name(site_name)
    if not source.is_request_url(request_url):
        return "Request URL not valid for %s" % site_name
    return source


# #### Route auxiliary functions

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = Download.query
    q = search_filter(q, search)
    q = default_order(q, search)
    return q


def create():
    global RECHECK_DOWNLOADS
    force_download = request.values.get('force', type=eval_bool_string)
    image_urls_only = request.values.get('image_urls_only', type=eval_bool_string)
    dataparams = get_data_params(request, 'download')
    createparams = convert_create_params(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = check_create_params(createparams)
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    if image_urls_only and len(createparams['image_urls']) == 0:
        return set_error(retdata, "No image URLs set!")
    if not force_download:
        check_download = uniqueness_check(createparams)
        if check_download is not None:
            retdata['item'] = check_download.to_json()
            return set_error(retdata, "Download already exists.")
    source = validate_request_url(createparams['request_url'])
    if isinstance(source, str):
        return set_error(retdata, source)
    createparams['image_urls'] = [url for url in createparams['image_urls'] if source.is_image_url(url)]
    download = create_download_from_parameters(createparams)
    retdata['item'] = download.to_json()
    SCHEDULER.add_job("process_download-%d" % download.id, process_download, args=(download.id,))
    if RECHECK_DOWNLOADS is None:
        RECHECK_DOWNLOADS = RepeatTimer(30, _recheck_pending_downloads)
        RECHECK_DOWNLOADS.setDaemon(True)
        RECHECK_DOWNLOADS.start()
    return retdata


def download_select():
    force_load = request.values.get('force', type=eval_bool_string)
    dataparams = get_data_params(request, 'download')
    selectparams = convert_data_params(dataparams)
    retdata = {'error': False, 'data': selectparams, 'params': dataparams}
    if 'request_url' not in selectparams:
        return set_error(retdata, "Request URL not specified.")
    selectparams['request_url'] = selectparams['request_url'].split('#')[0]
    check_download = uniqueness_check(selectparams)
    if check_download is not None and not force_load:
        retdata['item'] = check_download.to_json()
        return set_error(retdata, "Download already exists.")
    errors = check_create_params(selectparams)
    if len(errors):
        return set_error(retdata, '\n'.join(errors))
    source = validate_request_url(selectparams['request_url'])
    if isinstance(source, str):
        return set_error(retdata, source)
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

@bp.route('/downloads/<int:id>.json')
def show_json(id):
    return show_json_response(Download, id, options=JSON_OPTIONS)


@bp.route('/downloads/<int:id>')
def show_html(id):
    download = get_or_abort(Download, id, options=SHOW_HTML_OPTIONS)
    elements = download.elements_paginate(page=get_page(request),
                                          per_page=get_limit(request, max_limit=8),
                                          options=SHOW_ELEMENTS_HTML_OPTIONS)
    return render_template("downloads/show.html", download=download, elements=elements)


# ###### INDEX

@bp.route('/downloads.json', methods=['GET'])
def index_json():
    q = index()
    q = q.options(JSON_OPTIONS)
    return index_json_response(q, request)


@bp.route('/downloads', methods=['GET'])
def index_html():
    q = index()
    q = q.options(INDEX_HTML_OPTIONS)
    page = paginate(q, request)
    return index_html_response(page, 'download', 'downloads')


# ###### CREATE

@bp.route('/downloads/new', methods=['GET'])
def new_html():
    """HTML access point to create function."""
    form = get_download_form(**request.args)
    return render_template("downloads/new.html", form=form, download=Download())


@bp.route('/downloads', methods=['POST'])
def create_html():
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        data = {'noprocess': True, 'download[request_url]': results['data']['request_url']}
        if referrer_check('download.download_all_html', request):
            return redirect(url_for('download.download_all_html', **data))
        if referrer_check('download.download_select_html', request):
            return redirect(url_for('download.download_select_html', **data))
        return redirect(url_for('download.new_html', **results['data']))
    return redirect(url_for('download.show_html', id=results['item']['id']))


@bp.route('/downloads.json', methods=['POST'])
def create_json():
    return create()


# ###### MISC

@bp.route('/downloads/all', methods=['GET'])
def download_all_html():
    show_form = request.args.get('show_form', type=eval_bool_string)
    if show_form:
        return render_template("downloads/all.html", form=get_download_form(), download=Download())
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        form = get_download_form(**results['data'])
        if 'item' in results:
            download = Download.find(results['item']['id'])
        else:
            download = Download()
        return render_template("downloads/all.html", form=form, download=download)
    return redirect(url_for('download.show_html', id=results['item']['id']))


@bp.route('/downloads/select', methods=['GET'])
def download_select_html():
    show_form = request.args.get('show_form', type=eval_bool_string)
    if show_form:
        return render_template("downloads/select.html", illust_urls=None, form=get_download_form(), download=Download())
    results = download_select()
    form = get_download_form(request_url=results['data']['request_url'])
    if results['error']:
        flash(results['message'], 'error')
        if 'item' in results:
            download = Download.find(results['item']['id'])
        else:
            download = Download()
        return render_template("downloads/select.html", illust_urls=None, form=form, download=download)
    return render_template("downloads/select.html", form=form, illust_urls=results['item'], download=Download())


@bp.route('/downloads/<int:id>/check', methods=['POST'])
def download_check_html(id):
    get_or_abort(Download, id)
    SCHEDULER.add_job("process_download-%d" % id, process_download, args=(id,))
    return redirect(request.referrer)


@bp.route('/downloads/<int:id>/resubmit', methods=['POST'])
def resubmit_html(id):
    download = get_or_abort(Download, id)
    update_download_from_parameters(download, {'status_name': 'pending'})
    SCHEDULER.add_job("process_download-%d" % id, process_download, args=(id,))
    return redirect(request.referrer)


# #### Private

def _recheck_pending_downloads():
    global RECHECK_DOWNLOADS
    pending_downloads = get_pending_downloads()
    if len(pending_downloads) == 0 and RECHECK_DOWNLOADS is not None:
        print("\nDownloads recheck - exiting\n")
        RECHECK_DOWNLOADS.cancel()
        RECHECK_DOWNLOADS = None
    else:
        print("\nDownloads recheck - %d pending\n" % len(pending_downloads))
        for download in pending_downloads:
            if download.created < minutes_ago(1):
                job_id = "process_download-%d" % download.id
                if SCHEDULER.get_job(job_id) is None:
                    print_warning(f"Restarting stalled {download.shortlink}")
                    SCHEDULER.add_job(job_id, process_download, args=(download.id,))
    SESSION.remove()


def _initialize():
    timer = threading.Timer(30, _recheck_pending_downloads)
    timer.setDaemon(True)
    timer.start()


# ## INITIALIZE

if MAIN_PROCESS:
    _initialize()
