# APP/CONTROLLERS/TAGS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, flash, redirect

# ## PACKAGE IMPORTS
from utility.data import eval_bool_string, int_or_array

# ## LOCAL IMPORTS
from ..models import Tag, UserTag, PostTags, Post
from ..logical.utility import set_error
from ..logical.database.tag_db import create_tag_from_parameters
from ..logical.records.tag_rec import append_tag_to_item, remove_tag_from_item
from .base_controller import get_params_value, process_request_values, show_json_response, index_json_response,\
    search_filter, default_order, paginate, get_or_abort, get_data_params, check_param_requirements, parse_type,\
    render_template_ws, index_html_response


# ## GLOBAL VARIABLES

bp = Blueprint("tag", __name__)

APPEND_KEYS = ['post_id']

CREATE_REQUIRED_PARAMS = ['name', 'type']
POLYMORPHIC_TAG_TYPES = ['site_tag', 'user_tag']


# ## FUNCTIONS

# #### Helper functions

def uniqueness_check(dataparams):
    return Tag.query.filter(Tag.name == dataparams['name'], Tag.type_value == dataparams['type']).one_or_none()


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


def append_item(tag):
    retdata = {'error': False, 'item': tag.to_json()}
    if tag.type_name == 'site_tag':
        return set_error(retdata, "Site tags cannot be appended.")
    dataparams = get_data_params(request, 'tag')
    dataparams.update({k: parse_type(dataparams, k, int_or_array) for (k, v) in dataparams.items() if k in APPEND_KEYS})
    append_key = [key for key in APPEND_KEYS if key in dataparams and dataparams[key] is not None]
    if len(append_key) > 1:
        return set_error(retdata, "May append using only a single type; multiple values found: %s" % repr(append_key))
    if len(append_key) == 0:
        return set_error(retdata, "Must include an append type.")
    return append_tag_to_item(tag, append_key[0], dataparams)


def remove_item(tag):
    retdata = {'error': False, 'item': tag.to_json()}
    if tag.type_name == 'site_tag':
        return set_error(retdata, "Site tags cannot be removed.")
    dataparams = get_data_params(request, 'tag')
    dataparams.update({k: parse_type(dataparams, k, int) for (k, v) in dataparams.items() if k in APPEND_KEYS})
    remove_key = [key for key in APPEND_KEYS if key in dataparams and dataparams[key] is not None]
    if len(remove_key) > 1:
        return set_error(retdata, "May remove using only a single ID; multiple values found: %s" % repr(remove_key))
    elif len(remove_key) == 0:
        return set_error(retdata, "Must include an remove ID.")
    return remove_tag_from_item(tag, remove_key[0], dataparams)


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
    page = paginate(q, request)
    return index_html_response(page, 'tag', 'tags')


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


# ###### APPEND


@bp.route('/tags/<int:id>/append', methods=['POST'])
def append_item_show_html(id):
    tag = get_or_abort(Tag, id)
    results = append_item(tag)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash("Tag appended.")
    return redirect(request.referrer)


@bp.route('/tags/append', methods=['POST'])
def append_item_index_html():
    retdata = _get_user_tag()
    if retdata['error']:
        flash(retdata['message'], 'error')
        return redirect(request.referrer)
    results = append_item(retdata['tag'])
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash("Tag appended.")
    return redirect(request.referrer)


@bp.route('/tags/append.json', methods=['POST'])
def append_item_index_json():
    retdata = _get_user_tag()
    if retdata['error']:
        return retdata
    result = append_item(retdata['tag'])
    if result['error']:
        return result
    is_preview = request.values.get('preview', type=eval_bool_string, default=False)
    if is_preview:
        post = Post.find(result['append']['id'])
        tags = _get_user_tags_by_post_id(result['append']['id'])
        result['html'] = render_template_ws("tags/_section.html", tags=tags, section_id='tag-list', item=post)
    return result


# ###### REMOVE

@bp.route('/tags/<int:id>/remove', methods=['DELETE'])
def remove_item_show_html(id):
    tag = get_or_abort(Tag, id)
    results = remove_item(tag)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash("Tag removed.")
    return redirect(request.referrer)


@bp.route('/tags/<int:id>/remove.json', methods=['DELETE'])
def remove_item_show_json(id):
    tag = get_or_abort(Tag, id)
    result = remove_item(tag)
    if result['error']:
        return result
    is_preview = request.values.get('preview', type=eval_bool_string, default=False)
    if is_preview:
        post = Post.find(result['remove']['id'])
        tags = _get_user_tags_by_post_id(result['remove']['id'])
        result['html'] = render_template_ws("tags/_section.html", tags=tags, section_id='tag-list', item=post)
    return result


# #### Private

def _get_user_tag():
    retdata = {'error': False}
    tag_name = retdata['name'] = request.values.get('tag[name]')
    if tag_name is None:
        return set_error(retdata, "Tag name parameter not included.")
    tag = retdata['tag'] = Tag.query.filter(Tag.name == tag_name, Tag.type_value == 'user_tag').one_or_none()
    if tag is None:
        return set_error(retdata, "Tag with name %s not found." % tag_name)
    return retdata


def _get_user_tags_by_post_id(post_id):
    subquery = PostTags.query.filter(PostTags.post_id == post_id).with_entities(PostTags.tag_id)
    return UserTag.query.filter(UserTag.id.in_(subquery)).all()
