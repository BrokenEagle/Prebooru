# APP/CONTROLLERS/TAGS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, flash, redirect

# ## LOCAL IMPORTS
from ..models import Tag
from ..logical.utility import set_error
from ..logical.database.tag_db import create_tag_from_parameters
from .base_controller import get_params_value, process_request_values, show_json_response, index_json_response,\
    search_filter, default_order, paginate, get_or_abort, get_data_params, check_param_requirements


# ## GLOBAL VARIABLES

bp = Blueprint("tag", __name__)

CREATE_REQUIRED_PARAMS = ['name', 'type']
POLYMORPHIC_TAG_TYPES = ['site_tag', 'user_tag']


# ## FUNCTIONS

# #### Helper functions

def uniqueness_check(dataparams):
    return Tag.query.filter_by(name=dataparams['name'], type=dataparams['type']).first()


def validate_type(dataparams):
    return dataparams['type'] in POLYMORPHIC_TAG_TYPES


# #### Route helpers

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    negative_search = get_params_value(params, 'not', True)
    q = Tag.query
    q = search_filter(q, search, negative_search)
    q = default_order(q, search)
    return q


def create():
    dataparams = get_data_params(request, 'tag')
    retdata = {'error': False, 'params': dataparams}
    errors = check_param_requirements(dataparams, CREATE_REQUIRED_PARAMS)
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    if not validate_type(dataparams):
        return set_error(retdata, "'%s' is not a valid tag type." % dataparams['type'])
    check_tag = uniqueness_check(dataparams)
    if check_tag is not None:
        retdata['item'] = check_tag.to_json()
        return set_error(retdata, "Tag already exists: tag #%d" % check_tag.id)
    tag = create_tag_from_parameters(dataparams)
    retdata['item'] = tag.to_json()
    return retdata


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


# ###### CREATE

@bp.route('/tags', methods=['POST'])
def create_html():
    results = create()
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash("Tag created.")
    return redirect(request.referrer)


@bp.route('/tags.json', methods=['POST'])
def create_json():
    return create()

