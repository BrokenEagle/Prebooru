# APP/CONTROLLERS/POOLS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, abort, url_for, flash, redirect
from sqlalchemy.orm import selectinload
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired


# ## PACKAGE IMPORTS
from utility.data import eval_bool_string

# ## LOCAL IMPORTS
from ..models import Pool, Post, Illust, IllustUrl, PoolElement
from ..logical.utility import set_error
from ..logical.database.pool_db import create_pool_from_parameters, update_pool_from_parameters
from ..logical.searchable import numeric_matching
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_data_params, get_form, get_page, get_limit, get_or_abort,\
    get_or_error, check_param_requirements, nullify_blanks, parse_bool_parameter, set_default, index_html_response


# ## GLOBAL VARIABLES

bp = Blueprint("pool", __name__)

CREATE_REQUIRED_PARAMS = ['name', 'series']
VALUES_MAP = {
    **{k: k for k in Pool.__table__.columns.keys()},
}

# #### Load options

SHOW_HTML_OPTIONS = (
    selectinload(PoolElement.post).options(
        selectinload(Post.notations),
        selectinload(Post.illust_urls).selectinload(IllustUrl.illust),
    ),
    selectinload(PoolElement.illust).options(
        selectinload(Illust.urls).selectinload(IllustUrl.post),
        selectinload(Illust.notations),
    ),
    selectinload(PoolElement.notation)
)


# #### Form

FORM_CONFIG = {
    'name': {
        'field': StringField,
        'kwargs': {
            'validators': [DataRequired()],
        },
    },
    'series': {
        'field': BooleanField,
        'kwargs': {
            'description': "Enables pool navigation.",
        },
    },
}


# ## FUNCTIONS

# #### Helper functions

def get_pool_form(**kwargs):
    return get_form('pool', FORM_CONFIG, **kwargs)


def uniqueness_check(dataparams, pool):
    name = dataparams.get('name', pool.name)
    if name != pool.name:
        return Pool.query.filter_by(name=name).first()


def convert_data_params(dataparams):
    params = get_pool_form(**dataparams).data
    params['series'] = parse_bool_parameter(dataparams, 'series')
    params = nullify_blanks(params)
    return params


def convert_create_params(dataparams):
    createparams = convert_data_params(dataparams)
    set_default(createparams, 'series', False)
    return createparams


def convert_update_params(dataparams):
    updateparams = convert_data_params(dataparams)
    updatelist = [VALUES_MAP[key] for key in dataparams if key in VALUES_MAP]
    updateparams = {k: v for (k, v) in updateparams.items() if k in updatelist}
    return updateparams


# #### Route auxiliary functions

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = Pool.query
    q = search_filter(q, search)
    if 'post_id' in search:
        q = q.unique_join(PoolElement, Pool.elements)
        q = q.filter(PoolElement.type_value == 'pool_post')
        q = q.filter(numeric_matching(PoolElement, 'post_id', search['post_id']))
    elif 'illust_id' in search:
        q = q.unique_join(PoolElement, Pool.elements)
        q = q.filter(PoolElement.type_value == 'pool_illust')
        q = q.filter(numeric_matching(PoolElement, 'illust_id', search['illust_id']))
    elif 'notation_id' in search:
        q = q.unique_join(PoolElement, Pool.elements)
        q = q.filter(PoolElement.type_value == 'pool_notation')
        q = q.filter(numeric_matching(PoolElement, 'notation_id', search['notation_id']))
    if 'order' in search and search['order'] in ['updated']:
        q = q.order_by(Pool.updated.desc())
    else:
        q = default_order(q, search)
    return q


def create():
    dataparams = get_data_params(request, 'pool')
    createparams = convert_create_params(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = check_param_requirements(createparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    check_pool = uniqueness_check(createparams, Pool())
    if check_pool is not None:
        retdata['item'] = check_pool.to_json()
        return set_error(retdata, "Pool with name already exists: pool #%d" % check_pool.id)
    pool = create_pool_from_parameters(createparams)
    retdata['item'] = pool.to_json()
    return retdata


def update(pool):
    dataparams = get_data_params(request, 'pool')
    updateparams = convert_update_params(dataparams)
    retdata = {'error': False, 'data': updateparams, 'params': dataparams}
    check_pool = uniqueness_check(updateparams, pool)
    if check_pool is not None:
        retdata['item'] = check_pool.to_json()
        return set_error(retdata, "Pool with name already exists: pool #%d" % check_pool.id)
    update_pool_from_parameters(pool, updateparams)
    retdata['item'] = pool.to_json()
    return retdata


# #### Route functions

# ###### SHOW

@bp.route('/pools/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(Pool, id)


@bp.route('/pools/<int:id>', methods=['GET'])
def show_html(id):
    pool = get_or_abort(Pool, id)
    page = pool.element_paginate(pagenum=get_page(request), per_page=get_limit(request),
                                 options=SHOW_HTML_OPTIONS)
    edit_pool = request.values.get('edit_pool', type=eval_bool_string, default=False)
    return render_template("pools/show.html", pool=pool, page=page, edit_pool=edit_pool)


@bp.route('/pools/<int:id>/last', methods=['GET'])
def show_last_html(id):
    pool = get_or_abort(Pool, id)
    element_count = pool._get_element_count()
    last_page = ((element_count - 1) // get_limit(request)) + 1 if element_count > 0 else 1
    return redirect(url_for('pool.show_html', id=id, page=last_page, **request.args))


# ###### INDEX

@bp.route('/pools.json', methods=['GET'])
def index_json():
    q = index()
    return index_json_response(q, request)


@bp.route('/pools', methods=['GET'])
def index_html():
    q = index()
    page = paginate(q, request)
    return index_html_response(page, 'pool', 'pools')


# ###### CREATE

@bp.route('/pools/new', methods=['GET'])
def new_html():
    """HTML access point to create function."""
    form = get_pool_form(**request.args)
    return render_template("pools/new.html", form=form, pool=Pool())


@bp.route('/pools', methods=['POST'])
def create_html():
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('pool.new_html', **results['data']))
    return redirect(url_for('pool.show_html', id=results['item']['id']))


@bp.route('/pools.json', methods=['POST'])
def create_json():
    return create()


# ###### UPDATE

@bp.route('/pools/<int:id>/edit', methods=['GET'])
def edit_html(id):
    pool = Pool.find(id)
    if pool is None:
        abort(404)
    editparams = pool.to_json()
    form = get_pool_form(**editparams)
    return render_template("pools/edit.html", form=form, pool=pool)


@bp.route('/pools/<int:id>', methods=['PUT'])
def update_html(id):
    pool = get_or_abort(Pool, id)
    results = update(pool)
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('pool.edit_html', id=id))
    return redirect(url_for('pool.show_html', id=pool.id))


@bp.route('/pools/<int:id>', methods=['PUT'])
def update_json(id):
    pool = get_or_error(Pool, id)
    if type(pool) is dict:
        return pool
    return update(pool)
