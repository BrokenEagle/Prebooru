# APP/CONTROLLERS/SIMILARITY_MATCHES_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, flash, redirect, render_template
from sqlalchemy.orm import selectinload

# ## LOCAL IMPORTS
from ..models import SimilarityPoolElement
from ..logical.utility import search_url_for
from ..logical.database.similarity_match_db import delete_similarity_pool_element,\
    batch_delete_similarity_pool_element
from .base_controller import get_data_params, get_or_abort, parse_list_type, process_request_values, get_params_value,\
    search_filter, default_order, index_json_response, paginate, get_or_error, show_json_response


# ## GLOBAL VARIABLES

bp = Blueprint("similarity_pool_element", __name__)

INDEX_HTML_OPTIONS = (
    #selectinload(SimilarityPoolElement.pool).selectinload(SimilarityPool.post).lazyload('*'),
    selectinload(SimilarityPoolElement.post).lazyload('*'),
)

MAX_LIMIT_HTML = 100


# ## FUNCTIONS

# #### Route auxiliary functions

def index(is_json):
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    if not is_json:
        search['main'] = 'true'
    q = SimilarityPoolElement.query
    q = search_filter(q, search)
    q = default_order(q, search)
    return q


# #### Route functions

# ###### SHOW

@bp.route('/similarity_pool_elements/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(SimilarityPoolElement, id)


@bp.route('/similarity_pool_elements/<int:id>', methods=['GET'])
def show_html(id):
    return redirect(search_url_for('similarity_pool_element.index_html', id=id))


# ###### INDEX

@bp.route('/similarity_pool_elements.json', methods=['GET'])
def index_json():
    q = index(True)
    return index_json_response(q, request)


@bp.route('/similarity_pool_elements', methods=['GET'])
def index_html():
    q = index(False)
    q = q.options(INDEX_HTML_OPTIONS)
    similarity_pool_elements = paginate(q, request, MAX_LIMIT_HTML)
    return render_template("similarity_pool_elements/index.html",
                           similarity_pool_elements=similarity_pool_elements,
                           similarity_pool_element=SimilarityPoolElement())


# ###### DELETE

@bp.route('/similarity_pool_elements/<int:id>', methods=['DELETE'])
def delete_html(id):
    similarity_pool_element = get_or_abort(SimilarityPoolElement, id)
    delete_similarity_pool_element(similarity_pool_element)
    flash("Removed from post.")
    return redirect(request.referrer)


@bp.route('/similarity_pool_elements/<int:id>.json', methods=['DELETE'])
def delete_json(id):
    element = get_or_error(SimilarityPoolElement, id)
    if type(element) is dict:
        return element
    delete_similarity_pool_element(element)
    return {'error': False}


# ###### MISC

@bp.route('/similarity_pool_elements/batch_delete', methods=['POST'])
def batch_delete_html():
    dataparams = get_data_params(request, 'similarity_pool_element')
    dataparams['id'] = parse_list_type(dataparams, 'id', int)
    if dataparams['id'] is None or len(dataparams['id']) == 0:
        flash("Must include the IDs of the elements to delete.", 'error')
        return redirect(request.referrer)
    similarity_pool_elements = SimilarityPoolElement.query.filter(SimilarityPoolElement.id.in_(dataparams['id'])).all()
    if len(similarity_pool_elements) == 0:
        flash("Found no elements to delete with parameters.")
        return redirect(request.referrer)
    batch_delete_similarity_pool_element(similarity_pool_elements)
    flash("Removed elements from post.")
    return redirect(request.referrer)
