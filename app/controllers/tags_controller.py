# APP\CONTROLLERS\TAGS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template

# ## LOCAL IMPORTS
from ..models import Tag
from .base_controller import get_params_value, process_request_values, show_json_response, index_json_response, search_filter, default_order, paginate, get_or_abort


# ## GLOBAL VARIABLES

bp = Blueprint("tag", __name__)


# ## FUNCTIONS

# #### Route helpers

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    negative_search = get_params_value(params, 'not', True)
    q = Tag.query
    q = search_filter(q, search, negative_search)
    q = default_order(q, search)
    return q


# #### Route functions

# ###### SHOW

@bp.route('/tags/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(Tag, id)


@bp.route('/tags/<int:id>', methods=['GET'])
def show_html(id):
    tag = get_or_abort(Tag, id)
    return render_template("tags/show.html", tag=tag)


# ###### INDEX

@bp.route('/tags.json', methods=['GET'])
def index_json():
    q = index()
    return index_json_response(q, request)


@bp.route('/tags', methods=['GET'])
def index_html():
    q = index()
    tags = paginate(q, request)
    return render_template("tags/index.html", tags=tags, tag=Tag())
