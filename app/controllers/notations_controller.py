# APP\CONTROLLERS\NOTATIONS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, redirect, url_for, flash
from sqlalchemy import not_
from sqlalchemy.orm import selectinload
from wtforms import TextAreaField, IntegerField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS
from ..models import Notation, Pool, Artist, Illust, Post, PoolNotation
from ..logical.utility import EvalBoolString, IsFalsey
from ..database.notation_db import CreateNotationFromParameters, UpdateNotationFromParameters, AppendToItem, DeleteNotation
from .base_controller import ShowJson, IndexJson, SearchFilter, ProcessRequestValues, GetParamsValue, Paginate, DefaultOrder, GetDataParams, CustomNameForm,\
    GetOrAbort, HideInput, NullifyBlanks, CheckParamRequirements, SetError


# ## GLOBAL VARIABLES

bp = Blueprint("notation", __name__)

APPEND_KEYS = ['pool_id', 'artist_id', 'illust_id', 'post_id']

CREATE_REQUIRED_PARAMS = ['body']
VALUES_MAP = {
    **{k: k for k in Notation.__table__.columns.keys()},
    **{k: k for k in APPEND_KEYS},
}

NOTATION_POOLS_SUBQUERY = Notation.query.join(PoolNotation, Notation._pool).filter(Notation.id == PoolNotation.notation_id).with_entities(Notation.id)

APPEND_KEYS = ['pool_id', 'artist_id', 'illust_id', 'post_id']


# #### Load options

SHOW_HTML_OPTIONS = (
    selectinload(Notation._pool).selectinload(PoolNotation.pool),
    selectinload(Notation.artist),
    selectinload(Notation.illust),
    selectinload(Notation.post),
)


# ####Forms

def GetNotationForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class NotationForm(CustomNameForm):
        body = TextAreaField('Body', id='notation-body', custom_name='notation[body]', validators=[DataRequired()])
        pool_id = IntegerField('Pool ID', id='notation-pool-id', custom_name='notation[pool_id]')
        artist_id = IntegerField('Artist ID', id='notation-artist-id', custom_name='notation[artist_id]')
        illust_id = IntegerField('Illust ID', id='notation-illust-id', custom_name='notation[illust_id]')
        post_id = IntegerField('Post ID', id='notation-pool-id', custom_name='notation[post_id]')
    return NotationForm(**kwargs)


# ## FUNCTIONS

# #### Query functions

def PoolFilter(query, search):
    if 'has_pool' in search and EvalBoolString(search['has_pool']) is not None:
        subclause = Notation.id.in_(NOTATION_POOLS_SUBQUERY)
        if IsFalsey(search['has_pool']):
            subclause = not_(subclause)
        query = query.filter(subclause)
    elif 'pool_id' in search and search['pool_id'].isdigit():
        query = query.unique_join(PoolNotation, Notation._pool).filter(PoolNotation.pool_id == int(search['pool_id']))
    return query


# #### Helper functions

def AppendNewItems(notation, dataparams):
    retdata = {'error': False}
    append_key = [key for key in APPEND_KEYS if key in dataparams and dataparams[key] is not None]
    if len(append_key) > 1:
        return SetError(retdata, "May only append using the ID of a single entity; multiple values found: %s" % append_key)
    if len(append_key) == 1:
        return AppendToItem(notation, append_key[0], dataparams)
    return retdata


# #### Form functions

def HideNonGeneralInputs(form, item):
    append_key = item.__table__.name + '_id'
    for key in APPEND_KEYS:
        if key == append_key:
            HideInput(form, key, item.id)
        else:
            HideInput(form, key)


# #### Param functions

def ConvertDataParams(dataparams):
    params = GetNotationForm(**dataparams).data
    params = NullifyBlanks(params)
    return params


def ConvertCreateParams(dataparams):
    return ConvertDataParams(dataparams)


def ConvertUpdateParams(dataparams):
    updateparams = ConvertDataParams(dataparams)
    updatelist = [VALUES_MAP[key] for key in dataparams if key in VALUES_MAP or key in APPEND_KEYS]
    updateparams = {k: v for (k, v) in updateparams.items() if k in updatelist}
    return updateparams


# #### Route auxiliary functions

def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    q = Notation.query
    q = SearchFilter(q, search)
    q = PoolFilter(q, search)
    q = DefaultOrder(q, search)
    return q


def create():
    dataparams = GetDataParams(request, 'notation')
    createparams = ConvertCreateParams(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = CheckParamRequirements(createparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return SetError(retdata, '\n'.join(errors))
    notation = CreateNotationFromParameters(createparams)
    retdata.update(AppendNewItems(notation, createparams))
    retdata['item'] = notation.to_json()
    return retdata


def update(notation):
    dataparams = GetDataParams(request, 'notation')
    updateparams = ConvertUpdateParams(dataparams)
    retdata = {'error': False, 'data': updateparams, 'params': dataparams}
    UpdateNotationFromParameters(notation, updateparams)
    if notation.append_type is None:
        retdata.update(AppendNewItems(notation, updateparams))
    retdata['item'] = notation.to_json()
    return retdata


# #### Route functions

# ###### SHOW

@bp.route('/notations/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(Notation, id)


@bp.route('/notations/<int:id>', methods=['GET'])
def show_html(id):
    notation = GetOrAbort(Notation, id, options=SHOW_HTML_OPTIONS)
    return render_template("notations/show.html", notation=notation)


# ###### INDEX

@bp.route('/notations.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/notations', methods=['GET'])
def index_html():
    q = index()
    notations = Paginate(q, request)
    return render_template("notations/index.html", notations=notations, notation=Notation())


# ###### CREATE

@bp.route('/notations/new', methods=['GET'])
def new_html():
    form = GetNotationForm(**request.args)
    if form.pool_id.data:
        item = Pool.find(form.pool_id.data)
    elif form.artist_id.data:
        item = Artist.find(form.artist_id.data)
    elif form.illust_id.data:
        item = Illust.find(form.illust_id.data)
    elif form.post_id.data:
        item = Post.find(form.post_id.data)
    else:
        item = None
    if item is not None:
        HideNonGeneralInputs(form, item)
    return render_template("notations/new.html", form=form, item=item, notation=Notation())


@bp.route('/notations', methods=['POST'])
def create_html():
    results = create()
    if results['error']:
        flash(results['message'], 'error')
        return redirect(url_for('notation.new_html', **results['data']))
    return redirect(url_for('notation.show_html', id=results['item']['id']))


@bp.route('/notations.json', methods=['POST'])
def create_json():
    return create()


# ###### UPDATE

@bp.route('/notations/<int:id>/edit', methods=['GET'])
def edit_html(id):
    notation = GetOrAbort(Notation, id)
    editparams = notation.to_json()
    append_type = notation.append_type
    if append_type is not None:
        append_key = append_type + '_id'
        append_item = notation.append_item
        editparams[append_key] = append_item.id
    form = GetNotationForm(**editparams)
    if append_type is not None:
        HideNonGeneralInputs(form, append_item)
    return render_template("notations/edit.html", form=form, notation=notation)


@bp.route('/notations/<int:id>', methods=['PUT'])
def update_html(id):
    notation = GetOrAbort(Notation, id)
    results = update(notation)
    if results['error']:
        flash(results['message'], 'error')
    return redirect(url_for('notation.show_html', id=notation.id))


# ####DELETE

@bp.route('/notations/<int:id>', methods=['DELETE'])
def delete_html(id):
    notation = GetOrAbort(Notation, id)
    DeleteNotation(notation)
    flash("Notation deleted.")
    return redirect(url_for('notation.index_html'))
