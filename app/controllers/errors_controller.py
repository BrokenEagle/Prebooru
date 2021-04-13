# APP\CONTROLLERS\ERRORS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template

# ## LOCAL IMPORTS
from ..models import Error
from .base_controller import GetParamsValue, ProcessRequestValues, ShowJson, IndexJson, SearchFilter, DefaultOrder, Paginate,\
    GetOrAbort


# ## GLOBAL VARIABLES

bp = Blueprint("error", __name__)


# ## FUNCTIONS

# #### Route helpers

def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    q = Error.query
    q = SearchFilter(q, search)
    q = DefaultOrder(q, search)
    return q


# #### Route functions

# ###### SHOW

@bp.route('/errors/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Error, id)


@bp.route('/errors/<int:id>', methods=['GET'])
def show_html(id):
    error = GetOrAbort(Error, id)
    return render_template("errors/show.html", error=error)


# ###### INDEX

@bp.route('/errors.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/errors', methods=['GET'])
def index_html():
    q = index()
    errors = Paginate(q, request)
    return render_template("errors/index.html", errors=errors, error=Error())
