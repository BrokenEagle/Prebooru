# APP/CONTROLLERS/POOL_ELEMENTS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, redirect
from sqlalchemy.orm import selectinload

# ## PACKAGE IMPORTS
from utility.data import eval_bool_string

# ## LOCAL IMPORTS
from ..models import Pool, PoolElement
from ..logical.utility import set_error
from ..logical.records.pool_rec import add_element_to_pool
from ..logical.database.pool_element_db import delete_pool_element
from .base_controller import get_data_params, get_or_abort, get_or_error, check_param_requirements,\
    index_json_response, show_json_response, process_request_values, get_params_value, search_filter, default_order,\
    parse_type, render_template_ws


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

def check_create_params(dataparams):
    if (dataparams['illust_id'] is None) and (dataparams['post_id'] is None) and (dataparams['notation_id'] is None):
        return "No illust, post, or notation ID specified!"


def convert_data_params(dataparams):
    return {key: parse_type(dataparams, key, parser) for (key, parser) in PARSE_PARAMS_DICT.items()}


# #### Route auxiliary functions

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    negative_search = get_params_value(params, 'not', True)
    q = PoolElement.query
    q = search_filter(q, search, negative_search)
    q = default_order(q, search)
    return q


def create():
    dataparams = get_data_params(request, 'pool_element')
    createparams = convert_data_params(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = check_param_requirements(createparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    check = check_create_params(createparams)
    if check is not None:
        return set_error(retdata, check)
    pool = Pool.find(createparams['pool_id'])
    if pool is None:
        return set_error(retdata, "Pool #%d not found." % createparams['pool_id'])
    retdata.update(add_element_to_pool(pool, createparams))
    return retdata


# #### Route functions

# ###### SHOW

@bp.route('/pool_elements/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(PoolElement, id)


# ###### INDEX

@bp.route('/pool_elements.json', methods=['GET'])
def index_json():
    q = index()
    return index_json_response(q, request)


# ###### CREATE

@bp.route('/pool_elements.json', methods=['POST'])
def create_json():
    result = create()
    if result['error']:
        return result
    is_preview = request.values.get('preview', type=eval_bool_string, default=False)
    if is_preview:
        pool_elements = PoolElement.query.options(selectinload(PoolElement.pool))\
                                         .filter(PoolElement.id.in_(result['element_ids'])).all()
        result['html'] = render_template_ws("pools/_section.html", pool_elements=pool_elements,
                                            section_id=f"{result['type']}-pools")
    return result


# ###### DELETE

@bp.route('/pool_elements/<int:id>.json', methods=['DELETE'])
def delete_json(id):
    pool_element = get_or_error(PoolElement, id)
    if type(pool_element) is dict:
        return pool_element
    is_preview = request.values.get('preview', type=eval_bool_string, default=False)
    item_json = pool_element.item.basic_json()
    item_table = pool_element.item.table_name
    item_fkey = item_table + '_id'
    delete_pool_element(pool_element)
    retdata = {'error': False, 'type': item_table, 'item': item_json}
    if is_preview:
        pool_elements = PoolElement.query.options(selectinload(PoolElement.pool))\
                                         .filter(getattr(PoolElement, item_fkey) == item_json['id']).all()
        html = render_template_ws("pools/_section.html", pool_elements=pool_elements, section_id=f"{item_table}-pools")
        retdata['html'] = html
    return retdata


# ###### MISC

@bp.route('/pool_elements/<int:id>/previous', methods=['GET'])
def previous_html(id):
    pool_element = get_or_abort(PoolElement, id)
    previous_element = PoolElement.query.filter(PoolElement.pool_id == pool_element.pool_id,
                                                PoolElement.position < pool_element.position)\
                                  .order_by(PoolElement.position.desc()).first()
    if previous_element is None:
        return redirect(request.referrer)
    return redirect(previous_element.item.show_url)


@bp.route('/pool_elements/<int:id>/next', methods=['GET'])
def next_html(id):
    pool_element = get_or_abort(PoolElement, id)
    next_element = PoolElement.query.filter(PoolElement.pool_id == pool_element.pool_id,
                                            PoolElement.position > pool_element.position)\
                              .order_by(PoolElement.position.asc()).first()
    if next_element is None:
        return redirect(request.referrer)
    return redirect(next_element.item.show_url)
