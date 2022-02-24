# APP/CONTROLLERS/MEDIA_FILES_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template

# ## LOCAL IMPORTS
from ..models import MediaFile
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_or_abort


# ## GLOBAL VARIABLES

bp = Blueprint("media_file", __name__)


# ## FUNCTIONS

# #### Route auxiliary functions

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = MediaFile.query
    q = search_filter(q, search)
    q = default_order(q, search)
    return q


# #### Route functions

# ###### SHOW

@bp.route('/media_files/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(MediaFile, id)


@bp.route('/media_files/<int:id>', methods=['GET'])
def show_html(id):
    media_files = get_or_abort(MediaFile, id)
    return render_template("media_files/show.html", media_file=media_files)


# ###### INDEX

@bp.route('/media_files.json', methods=['GET'])
def index_json():
    q = index()
    return index_json_response(q, request)


@bp.route('/media_files', methods=['GET'])
def index_html():
    q = index()
    media_files = paginate(q, request)
    return render_template("media_files/index.html", media_files=media_files, media_file=MediaFile())
