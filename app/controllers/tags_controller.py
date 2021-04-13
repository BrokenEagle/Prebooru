# APP\CONTROLLERS\TAGS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template

# ## LOCAL IMPORTS
from ..models import Tag
from .base_controller import GetParamsValue, ProcessRequestValues, ShowJson, IndexJson, SearchFilter, DefaultOrder, Paginate, GetOrAbort


# ## GLOBAL VARIABLES

bp = Blueprint("tag", __name__)


# ## FUNCTIONS

# #### Route helpers

def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    negative_search = GetParamsValue(params, 'not', True)
    q = Tag.query
    q = SearchFilter(q, search, negative_search)
    q = DefaultOrder(q, search)
    return q


# #### Route functions

# ###### SHOW

@bp.route('/tags/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Tag, id)


@bp.route('/tags/<int:id>', methods=['GET'])
def show_html(id):
    tag = GetOrAbort(Tag, id)
    return render_template("tags/show.html", tag=tag)


# ###### INDEX

@bp.route('/tags.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/tags', methods=['GET'])
def index_html():
    q = index()
    tags = Paginate(q, request)
    return render_template("tags/index.html", tags=tags, tag=Tag())
