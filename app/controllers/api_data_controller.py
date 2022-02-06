# APP/CONTROLLERS/API_DATA_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, url_for, redirect, flash

# ## LOCAL IMPORTS
from ..models import ApiData
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_or_abort


# ## GLOBAL VARIABLES

bp = Blueprint("api_data", __name__)


# ## FUNCTIONS

# #### Route auxiliary functions

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = ApiData.query
    q = search_filter(q, search)
    q = default_order(q, search)
    return q


# #### Route functions

# ###### SHOW

@bp.route('/api_data/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(ApiData, id)


@bp.route('/api_data/<int:id>', methods=['GET'])
def show_html(id):
    api_data = get_or_abort(ApiData, id)
    return render_template("api_data/show.html", api_datum=api_data)


# ###### INDEX

@bp.route('/api_data.json', methods=['GET'])
def index_json():
    q = index()
    return index_json_response(q, request)


@bp.route('/api_data', methods=['GET'])
def index_html():
    q = index()
    api_data = paginate(q, request)
    return render_template("api_data/index.html", api_data=api_data, api_datum=ApiData())
