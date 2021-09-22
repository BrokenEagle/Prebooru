# APP\CONTROLLERS\ERRORS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template

# ## LOCAL IMPORTS
from ..models import Error
from .base_controller import get_params_value, process_request_values, show_json, index_json, search_filter, default_order, paginate,\
    get_or_abort


# ## GLOBAL VARIABLES

bp = Blueprint("error", __name__)


# ## FUNCTIONS

# #### Route helpers

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = Error.query
    q = search_filter(q, search)
    q = default_order(q, search)
    return q


# #### Route functions

# ###### SHOW

@bp.route('/errors/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json(Error, id)


@bp.route('/errors/<int:id>', methods=['GET'])
def show_html(id):
    error = get_or_abort(Error, id)
    return render_template("errors/show.html", error=error)


# ###### INDEX

@bp.route('/errors.json', methods=['GET'])
def index_json():
    q = index()
    return index_json(q, request)


@bp.route('/errors', methods=['GET'])
def index_html():
    q = index()
    errors = paginate(q, request)
    return render_template("errors/index.html", errors=errors, error=Error())
