# APP/CONTROLLERS/UPLOAD_ELEMENTS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template
from sqlalchemy.orm import selectinload

# ## LOCAL IMPORTS
from ..models import UploadElement, IllustUrl, Illust
from .base_controller import get_params_value, process_request_values, show_json_response, index_json_response,\
    search_filter, default_order, paginate, get_or_abort, index_html_response


# ## GLOBAL VARIABLES

bp = Blueprint("upload_element", __name__)

# #### Load options

SHOW_HTML_OPTIONS = (
    selectinload(UploadElement.illust_url).options(
        selectinload(IllustUrl.illust).selectinload(Illust.artist).lazyload('*'),
        selectinload(IllustUrl.post).lazyload('*'),
    ),
)

INDEX_HTML_OPTIONS = (
    selectinload(UploadElement.illust_url).selectinload(IllustUrl.post).lazyload('*'),
    selectinload(UploadElement.errors),
)


# ## FUNCTIONS

# #### Route helpers

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = UploadElement.query
    q = search_filter(q, search)
    q = default_order(q, search)
    return q


# ###### SHOW

@bp.route('/upload_elements/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(UploadElement, id)


@bp.route('/upload_elements/<int:id>', methods=['GET'])
def show_html(id):
    upload_element = get_or_abort(UploadElement, id, options=SHOW_HTML_OPTIONS)
    return render_template("upload_elements/show.html", upload_element=upload_element)


# ###### INDEX

@bp.route('/upload_elements.json', methods=['GET'])
def index_json():
    q = index()
    return index_json_response(q, request)


@bp.route('/upload_elements', methods=['GET'])
def index_html():
    q = index()
    q = q.options(INDEX_HTML_OPTIONS)
    page = paginate(q, request)
    return index_html_response(page, 'upload_element', 'upload_elements')
