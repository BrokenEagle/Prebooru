# APP/CONTROLLERS/SIMILARITY_POOLS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template
from sqlalchemy.orm import selectinload

# ## LOCAL IMPORTS
from ..models import SimilarityPool, SimilarityPoolElement
from .base_controller import show_json_response, get_page, get_limit, get_or_abort, process_request_values,\
    get_params_value, search_filter, default_order, paginate, index_json_response


# ## GLOBAL VARIABLES

bp = Blueprint("similarity_pool", __name__)

# #### Load options

INDEX_HTML_OPTIONS = (
    selectinload(SimilarityPool.post).lazyload('*'),
    selectinload(SimilarityPool.elements).selectinload(SimilarityPoolElement.post).lazyload('*'),
)

MAX_LIMIT_HTML = 50


# ## FUNCTIONS

# #### Route auxiliary functions

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = SimilarityPool.query
    q = search_filter(q, search)
    q = default_order(q, search)
    return q


# #### Route functions

# ###### SHOW

@bp.route('/similarity_pools/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(SimilarityPool, id)


@bp.route('/similarity_pools/<int:id>', methods=['GET'])
def show_html(id):
    similarity_pool = get_or_abort(SimilarityPool, id)
    elements = similarity_pool.element_paginate(page=get_page(request), per_page=get_limit(request))
    return render_template("similarity_pools/show.html", similarity_pool=similarity_pool, elements=elements)


# ###### INDEX

@bp.route('/similarity_pools.json', methods=['GET'])
def index_json():
    q = index()
    return index_json_response(q, request)


@bp.route('/similarity_pools', methods=['GET'])
def index_html():
    q = index()
    q = q.options(INDEX_HTML_OPTIONS)
    similarity_pools = paginate(q, request, MAX_LIMIT_HTML)
    return render_template("similarity_pools/index.html", similarity_pools=similarity_pools,
                           similarity_pool=SimilarityPool())
