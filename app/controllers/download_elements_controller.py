# APP/CONTROLLERS/DOWNLOAD_ELEMENTS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template
from sqlalchemy.orm import selectinload

# ## LOCAL IMPORTS
from ..models import DownloadElement, IllustUrl
from ..logical.database.download_element_db import update_download_element_from_parameters
from ..logical.records.download_rec import process_network_download
from .base_controller import get_params_value, process_request_values, show_json_response, index_json_response,\
    search_filter, default_order, paginate, get_or_abort, index_html_response


# ## GLOBAL VARIABLES

bp = Blueprint("download_element", __name__)

# #### Load options

SHOW_HTML_OPTIONS = (
    selectinload(DownloadElement.illust_url).selectinload(IllustUrl.post).lazyload('*'),
    selectinload(DownloadElement.errors),
)

INDEX_HTML_OPTIONS = (
    selectinload(DownloadElement.illust_url).selectinload(IllustUrl.post).lazyload('*'),
    selectinload(DownloadElement.errors),
)


# ## FUNCTIONS

# #### Route helpers

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = DownloadElement.query
    q = search_filter(q, search)
    q = default_order(q, search)
    return q


# ###### SHOW

@bp.route('/download_elements/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(DownloadElement, id)


@bp.route('/download_elements/<int:id>', methods=['GET'])
def show_html(id):
    download_element = get_or_abort(DownloadElement, id, options=SHOW_HTML_OPTIONS)
    return render_template("download_elements/show.html", download_element=download_element)


# ###### INDEX

@bp.route('/download_elements.json', methods=['GET'])
def index_json():
    q = index()
    return index_json_response(q, request)


@bp.route('/download_elements', methods=['GET'])
def index_html():
    q = index()
    q = q.options(INDEX_HTML_OPTIONS)
    page = paginate(q, request)
    return index_html_response(page, 'download_element', 'download_elements')


# ###### MISC

@bp.route('/download_elements/<int:id>/redownload', methods=['POST'])
def redownload_html(id):
    download_element = get_or_abort(DownloadElement, id)
    update_download_element_from_parameters(download_element, {'status_name': 'pending'})
    create_post_from_download_element(download_element)
    return redirect(request.referrer)
