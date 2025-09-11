# APP/CONTROLLERS/NOTATIONS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, redirect, url_for, flash
from sqlalchemy import not_
from sqlalchemy.orm import selectinload
from wtforms import TextAreaField, IntegerField
from wtforms.validators import DataRequired

# ## PACKAGE IMPORTS
from utility.data import eval_bool_string, is_falsey

# ## LOCAL IMPORTS
from ..models import Notation, Pool, Subscription, Booru, Artist, Illust, Post, PoolElement, TABLES
from ..logical.utility import set_error
from ..logical.database.notation_db import create_notation_from_parameters, update_notation_from_parameters
from ..logical.records.notation_rec import append_notation_to_item, delete_notation
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_data_params, get_form, get_or_abort, hide_input,\
    nullify_blanks, check_param_requirements, index_html_response, redirect_url, redirect_html_response


# ## GLOBAL VARIABLES

bp = Blueprint("notation", __name__)

APPEND_KEYS = ['pool_id', 'subscription_id', 'booru_id', 'artist_id', 'illust_id', 'post_id']

CREATE_REQUIRED_PARAMS = ['body']
VALUES_MAP = {
    **{k: k for k in Notation.__table__.columns.keys()},
    **{'pool_id': 'pool_id'},
}

NOTATION_POOLS_SUBQUERY = Notation.query.join(PoolElement, Notation.pool_element)\
                                        .filter(Notation.id == PoolElement.notation_id,
                                                PoolElement.type_value == 'pool_notation')\
                                        .with_entities(Notation.id)


# #### Load options

SHOW_HTML_OPTIONS = (
    selectinload(Notation.pool_element).selectinload(PoolElement.pool),
    selectinload(Notation.booru),
    selectinload(Notation.artist),
    selectinload(Notation.illust),
    selectinload(Notation.post),
)


# #### Form

FORM_CONFIG = {
    'body': {
        'field': TextAreaField,
        'kwargs': {
            'validators': [DataRequired()],
        },
    },
    'pool_id': {
        'name': 'Pool ID',
        'field': IntegerField,
    },
    'subscription_id': {
        'name': 'Booru ID',
        'field': IntegerField,
    },
    'booru_id': {
        'name': 'Booru ID',
        'field': IntegerField,
    },
    'artist_id': {
        'name': 'Artist ID',
        'field': IntegerField,
    },
    'illust_id': {
        'name': 'Illust ID',
        'field': IntegerField,
    },
    'post_id': {
        'name': 'Post ID',
        'field': IntegerField,
    },
}


# ## FUNCTIONS

# #### Query functions

def pool_filter(query, search):
    if 'has_pool' in search and eval_bool_string(search['has_pool']) is not None:
        subclause = Notation.id.in_(NOTATION_POOLS_SUBQUERY)
        if is_falsey(search['has_pool']):
            subclause = not_(subclause)
        query = query.filter(subclause)
    elif 'pool_id' in search and search['pool_id'].isdigit():
        query = query.unique_join(PoolElement, Notation.pool_element)
        query = query.filter(PoolElement.pool_id == int(search['pool_id']), PoolElement.type_value == 'pool_notation')
    return query


# #### Helper functions

def get_notation_form(**kwargs):
    return get_form('notation', FORM_CONFIG, **kwargs)


def append_new_items(notation, dataparams):
    retdata = {'error': False}
    append_key = [key for key in APPEND_KEYS if key in dataparams and dataparams[key] is not None]
    if len(append_key) > 1:
        msg = "May only append using the ID of a single entity; multiple values found: %s" % append_key
        return set_error(retdata, msg)
    if len(append_key) == 1:
        return append_notation_to_item(notation, append_key[0], dataparams)
    return retdata


# #### Form functions

def hide_nongeneral_inputs(form, item):
    append_key = item.__table__.name + '_id'
    for key in APPEND_KEYS:
        if key == append_key:
            hide_input(form, key, item.id)
        else:
            hide_input(form, key)


# #### Param functions

def convert_data_params(dataparams):
    params = get_notation_form(**dataparams).data
    params = nullify_blanks(params)
    return params


def convert_create_params(dataparams):
    return convert_data_params(dataparams)


def convert_update_params(dataparams):
    updateparams = convert_data_params(dataparams)
    updatelist = [VALUES_MAP[key] for key in dataparams if key in VALUES_MAP or key in APPEND_KEYS]
    updateparams = {k: v for (k, v) in updateparams.items() if k in updatelist}
    return updateparams


# #### Route auxiliary functions

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = Notation.query
    q = search_filter(q, search)
    q = pool_filter(q, search)
    q = default_order(q, search)
    return q


def create():
    dataparams = get_data_params(request, 'notation')
    createparams = convert_create_params(dataparams)
    retdata = {'error': False, 'data': createparams, 'params': dataparams}
    errors = check_param_requirements(createparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    notation = create_notation_from_parameters(createparams)
    retdata.update(append_new_items(notation, createparams))
    retdata['item'] = notation.to_json()
    return retdata


def update(notation):
    dataparams = get_data_params(request, 'notation')
    updateparams = convert_update_params(dataparams)
    retdata = {'error': False, 'data': updateparams, 'params': dataparams}
    update_notation_from_parameters(notation, updateparams)
    if notation.append_type is None:
        retdata.update(append_new_items(notation, updateparams))
    retdata['item'] = notation.to_json()
    return retdata


# #### Route functions

# ###### SHOW

@bp.route('/notations/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(Notation, id)


@bp.route('/notations/<int:id>', methods=['GET'])
def show_html(id):
    notation = get_or_abort(Notation, id, options=SHOW_HTML_OPTIONS)
    return render_template("notations/show.html", notation=notation)


# ###### INDEX

@bp.route('/notations.json', methods=['GET'])
def index_json():
    q = index()
    return index_json_response(q, request)


@bp.route('/notations', methods=['GET'])
def index_html():
    q = index()
    page = paginate(q, request)
    return index_html_response(page, 'notation', 'notations')


# ###### CREATE

@bp.route('/notations/new', methods=['GET'])
def new_html():
    form = get_notation_form(**request.args)
    if form.pool_id.data:
        item = Pool.find(form.pool_id.data)
    elif form.subscription_id.data:
        item = Subscription.find(form.subscription_id.data)
    elif form.booru_id.data:
        item = Booru.find(form.booru_id.data)
    elif form.artist_id.data:
        item = Artist.find(form.artist_id.data)
    elif form.illust_id.data:
        item = Illust.find(form.illust_id.data)
    elif form.post_id.data:
        item = Post.find(form.post_id.data)
    else:
        item = None
    if item is not None:
        hide_nongeneral_inputs(form, item)
    return render_template("notations/new.html", form=form, item=item, notation=Notation(),
                           redirect_url=redirect_url())


@bp.route('/notations', methods=['POST'])
def create_html():
    results = create()
    return redirect_html_response('notation', 'new_html', results)


@bp.route('/notations.json', methods=['POST'])
def create_json():
    return create()


# ###### UPDATE

@bp.route('/notations/<int:id>/edit', methods=['GET'])
def edit_html(id):
    notation = get_or_abort(Notation, id)
    editparams = notation.to_json()
    append_type = notation.append_type
    if append_type is not None:
        append_key = append_type + '_id'
        append_item = notation.append_item
        editparams[append_key] = append_item.id
    form = get_notation_form(**editparams)
    if append_type is not None:
        hide_nongeneral_inputs(form, append_item)
    return render_template("notations/edit.html", form=form, notation=notation, redirect_url=redirect_url())


@bp.route('/notations/<int:id>', methods=['PUT'])
def update_html(id):
    notation = get_or_abort(Notation, id)
    results = update(notation)
    return redirect_html_response('notation', 'edit_html', results)


# #### DELETE

@bp.route('/notations/<int:id>', methods=['DELETE'])
def delete_html(id):
    notation = get_or_abort(Notation, id)
    delete_notation(notation)
    flash("Notation deleted.")
    if request.args.get('redirect', type=eval_bool_string, default=False):
        return redirect(request.referrer)
    return redirect(url_for('notation.index_html'))
