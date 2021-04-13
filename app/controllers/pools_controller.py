# APP\CONTROLLERS\POOLS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, abort, url_for, flash, redirect
from sqlalchemy.orm import selectinload
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired


# ## LOCAL IMPORTS
from ..models import Pool, Post, Illust, IllustUrl, PoolPost, PoolIllust, PoolNotation
from ..database.pool_db import CreatePoolFromParameters, UpdatePoolFromParameters
from ..logical.searchable import NumericMatching
from .base_controller import ShowJson, IndexJson, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate,\
    DefaultOrder, GetDataParams, CustomNameForm, GetPage, GetLimit, GetOrAbort, GetOrError, CheckParamRequirements,\
    NullifyBlanks, SetError, ParseBoolParameter, SetDefault


# ## GLOBAL VARIABLES

bp = Blueprint("pool", __name__)

CREATE_REQUIRED_PARAMS = ['name', 'series']
VALUES_MAP = {
    **{k: k for k in Pool.__table__.columns.keys()},
}

# #### Load options

SHOW_HTML_ILLUST_OPTIONS = (
    selectinload(Illust.urls).selectinload(IllustUrl.post),
    selectinload(Illust.notations),
)

SHOW_HTML_POST_OPTIONS = (
    selectinload(Post.notations),
    selectinload(Post.illust_urls).selectinload(IllustUrl.illust),
)


# #### Forms

def GetPoolForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class PoolForm(CustomNameForm):
        name = StringField('Name', id='pool-name', custom_name='pool[name]', validators=[DataRequired()])
        series = BooleanField('Series', id='pool-series', custom_name='pool[series]', description="Enables pool navigation.")
    return PoolForm(**kwargs)


# ## FUNCTIONS

# #### Helper functions

def UniquenessCheck(dataparams, pool):
    name = dataparams['name'] if 'name' in dataparams else pool.name
    if name != pool.name:
        return Pool.query.filter_by(name=name).first()


def ConvertDataParams(dataparams):
    params = GetPoolForm(**dataparams).data
    params['series'] = ParseBoolParameter(dataparams, 'series')
    params = NullifyBlanks(params)
    return params


def ConvertCreateParams(dataparams):
    createparams = ConvertDataParams(dataparams)
    SetDefault(createparams, 'series', False)
    return createparams


def ConvertUpdateParams(dataparams):
    updateparams = ConvertDataParams(dataparams)
    updatelist = [VALUES_MAP[key] for key in dataparams if key in VALUES_MAP]
    updateparams = {k: v for (k, v) in updateparams.items() if k in updatelist}
    return updateparams


# #### Route auxiliary functions

def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    q = Pool.query
    q = SearchFilter(q, search)
    if 'post_id' in search:
        q = q.unique_join(PoolPost, Pool._elements)
        q = q.filter(NumericMatching(PoolPost, 'post_id', search['post_id']))
    elif 'illust_id' in search:
        q = q.unique_join(PoolIllust, Pool._elements)
        q = q.filter(NumericMatching(PoolIllust, 'illust_id', search['illust_id']))
    elif 'notation_id' in search:
        q = q.unique_join(PoolNotation, Pool._elements)
        q = q.filter(NumericMatching(PoolNotation, 'notation_id', search['notation_id']))
    if 'order' in search and search['order'] in ['updated']:
        q = q.order_by(Pool.updated.desc())
    else:
        q = DefaultOrder(q, search)
    return q


def create():
    dataparams = GetDataParams(request, 'pool')
    createparams = ConvertCreateParams(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = CheckParamRequirements(createparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return SetError(retdata, '\n'.join(errors))
    check_pool = UniquenessCheck(createparams, Pool())
    if check_pool is not None:
        retdata['item'] = check_pool.to_json()
        return SetError(retdata, "Pool with name already exists: pool #%d" % check_pool.id)
    pool = CreatePoolFromParameters(createparams)
    retdata['item'] = pool.to_json()
    return retdata


def update(pool):
    dataparams = GetDataParams(request, 'pool')
    updateparams = ConvertUpdateParams(dataparams)
    retdata = {'error': False, 'data': updateparams, 'params': dataparams}
    check_pool = UniquenessCheck(updateparams, pool)
    if check_pool is not None:
        retdata['item'] = check_pool.to_json()
        return SetError(retdata, "Pool with name already exists: pool #%d" % check_pool.id)
    UpdatePoolFromParameters(pool, updateparams)
    retdata['item'] = pool.to_json()
    return retdata


# #### Route functions

# ###### SHOW

@bp.route('/pools/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Pool, id)


@bp.route('/pools/<int:id>', methods=['GET'])
def show_html(id):
    pool = GetOrAbort(Pool, id)
    elements = pool.element_paginate(page=GetPage(request), per_page=GetLimit(request), illust_options=SHOW_HTML_ILLUST_OPTIONS, post_options=SHOW_HTML_POST_OPTIONS)
    return render_template("pools/show.html", pool=pool, elements=elements)


# ###### INDEX

@bp.route('/pools.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/pools', methods=['GET'])
def index_html():
    q = index()
    pools = Paginate(q, request)
    return render_template("pools/index.html", pools=pools, pool=Pool())


# ###### CREATE

@bp.route('/pools/new', methods=['GET'])
def new_html():
    """HTML access point to create function."""
    form = GetPoolForm(**request.args)
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
    form = GetPoolForm(name=pool.name)
    return render_template("pools/edit.html", form=form, pool=pool)


@bp.route('/pools/<int:id>', methods=['PUT'])
def update_html(id):
    pool = GetOrAbort(Pool, id)
    results = update(pool)
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('pool.edit_html', id=id))
    return redirect(url_for('pool.show_html', id=pool.id))


@bp.route('/pools/<int:id>', methods=['PUT'])
def update_json(id):
    pool = GetOrError(Pool, id)
    if type(pool) is dict:
        return pool
    return update(pool)
