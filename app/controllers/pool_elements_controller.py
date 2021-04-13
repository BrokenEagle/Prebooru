# APP\CONTROLLERS\POOL_ELEMENTS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, url_for, flash, redirect

# ## LOCAL IMPORTS
from ..models import Pool, PoolElement
from ..database.pool_element_db import CreatePoolElementFromParameters, DeletePoolElement
from .base_controller import GetDataParams, GetOrAbort, GetOrError, CheckParamRequirements, SetError, IndexJson, ShowJson,\
    ProcessRequestValues, GetParamsValue, SearchFilter, DefaultOrder, ParseType


# ## GLOBAL VARIABLES

bp = Blueprint("pool_element", __name__)

CREATE_REQUIRED_PARAMS = ['pool_id']

APPEND_KEYS = ['illust_id', 'post_id', 'notation_id']

PARSE_PARAMS_DICT = {
    'pool_id': int,
    'illust_id': int,
    'post_id': int,
    'notation_id': int,
}


# ## FUNCTIONS

# #### Helper functions

def CheckCreateParams(dataparams):
    if (dataparams['illust_id'] is None) and (dataparams['post_id'] is None) and (dataparams['notation_id'] is None):
        return "No illust, post, or notation ID specified!"


def ConvertDataParams(dataparams):
    return {key: ParseType(dataparams, key, parser) for (key, parser) in PARSE_PARAMS_DICT.items()}


# #### Route auxiliary functions

def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    negative_search = GetParamsValue(params, 'not', True)
    q = PoolElement.query
    q = SearchFilter(q, search, negative_search)
    q = DefaultOrder(q, search)
    return q


def create():
    dataparams = GetDataParams(request, 'pool_element')
    createparams = ConvertDataParams(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = CheckParamRequirements(createparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return SetError(retdata, '\n'.join(errors))
    check = CheckCreateParams(createparams)
    if check is not None:
        return SetError(retdata, check)
    pool = Pool.find(createparams['pool_id'])
    if pool is None:
        return SetError(retdata, "Pool #d not found." % createparams['pool_id'])
    retdata.update(CreatePoolElementFromParameters(pool, createparams))
    return retdata


def delete(pool_element):
    DeletePoolElement(pool_element)


# #### Route functions

# ###### SHOW

@bp.route('/pool_elements/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(PoolElement, id)


# ###### INDEX

@bp.route('/pool_elements.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


# ###### CREATE

@bp.route('/pool_elements', methods=['POST'])
def create_html():
    result = create()
    if result['error']:
        flash(result['message'], 'error')
        return redirect(request.referrer)
    flash("Added to pool.")
    return redirect(url_for('%s.show_html' % result['type'], id=result['item']['id']))


@bp.route('/pool_elements.json', methods=['POST'])
def create_json():
    return create()


# ###### DELETE

@bp.route('/pool_elements/<int:id>', methods=['DELETE'])
def delete_html(id):
    pool_element = GetOrAbort(PoolElement, id)
    delete(pool_element)
    flash("Removed from pool.")
    return redirect(request.referrer)


@bp.route('/pool_elements/<int:id>.json', methods=['DELETE'])
def delete_json(id):
    pool_element = GetOrError(PoolElement, id)
    if type(pool_element) is dict:
        return pool_element
    return {'error': False}


# ###### MISC

@bp.route('/pool_elements/<int:id>/previous', methods=['GET'])
def previous_html(id):
    pool_element = GetOrAbort(PoolElement, id)
    previous_element = PoolElement.query.filter(PoolElement.pool_id == pool_element.pool_id, PoolElement.position < pool_element.position).order_by(PoolElement.position.desc()).first()
    if previous_element is None:
        return redirect(request.referrer)
    return redirect(previous_element.item.show_url)


@bp.route('/pool_elements/<int:id>/next', methods=['GET'])
def next_html(id):
    pool_element = GetOrAbort(PoolElement, id)
    next_element = PoolElement.query.filter(PoolElement.pool_id == pool_element.pool_id, PoolElement.position > pool_element.position).order_by(PoolElement.position.asc()).first()
    if next_element is None:
        return redirect(request.referrer)
    return redirect(next_element.item.show_url)
