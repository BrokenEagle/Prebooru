# APP/CONTROLLERS/IMAGE_HASHES_CONTROLLER.PY

# ## PYTHON IMPORTS
from types import SimpleNamespace

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, flash, redirect
from wtforms import TextAreaField, FloatField, SelectField
from wtforms.validators import DataRequired

# ## LOCAL IMPORTS
from .. import SESSION
from ..models import Post
from ..logical.utility import set_error
from ..logical.database.post_db import get_posts_by_id
from ..logical.database.image_hash_db import delete_image_hash_by_post_id
from ..logical.database.similarity_match_db import delete_similarity_matches_by_post_id
from ..logical.records.image_hash_rec import check_all_image_urls_for_matches, generate_post_image_hashes
from ..logical.records.similarity_match_rec import generate_similarity_matches
from .base_controller import process_request_values, parse_type, parse_string_list, nullify_blanks, set_default,\
    check_param_requirements, eval_bool_string, jsonify_data, get_form


# ## GLOBAL VARIABLES

bp = Blueprint("image_hash", __name__)


# #### Form

FORM_CONFIG = {
    'urls_string': {
        'name': 'Urls',
        'field': TextAreaField,
        'kwargs': {
            'validators': [DataRequired()],
            'description': "Separated by carriage returns.",
        },
    },
    'score': {
        'field': FloatField,
        'kwargs': {
            'description': "Lowest score of results to return. Default is 90.0.",
        },
    },
    'size': {
        'name': 'Image size',
        'field': SelectField,
        'kwargs': {
            'choices': [("", ""), ('actual', 'Actual'), ('original', 'Original'), ('large', 'Large'),
                        ('medium', 'medium'), ('small', 'Small'), ('thumb', 'Thumb')],
        },
    },
    'sim_clause': {
        'name': 'Image size',
        'field': SelectField,
        'kwargs': {
            'choices': [("", ""), ('chunk', 'Chunk'), ('cross0', 'Cross #0'), ('cross0', 'Cross #1'),
                        ('cross2', 'Cross #2'), ('all', 'All')],
        },
    },
}


# ## FUNCTIONS

# #### Helper functions

def get_image_hash_form(**kwargs):
    return get_form('image_hash', FORM_CONFIG, **kwargs)


def convert_data_params(dataparams):
    params = get_image_hash_form(**dataparams.get('image_hash', {})).data
    if 'urls' in dataparams:
        params['urls'] = dataparams['urls']
    elif 'urls_string' in params:
        params['urls'] = parse_string_list(params, 'urls_string', r'\r?\n')
    else:
        params['urls'] = None
    params['score'] = parse_type(dataparams, 'score', float)
    params = nullify_blanks(params)
    set_default(params, 'score', 90.0)
    set_default(params, 'size', 'small')
    set_default(params, 'sim_clause', 'cross2')
    return params


# #### Route auxiliary functions

def check(include_posts):
    params = process_request_values(request.args)
    dataparams = convert_data_params(params)
    retdata = {'error': False, 'data': dataparams, 'params': params}
    errors = check_param_requirements(dataparams, ['urls'])
    if len(errors) > 0:
        return set_error(retdata, '\n'.join(errors))
    dataparams['url_string'] = '\r\n'.join(dataparams['urls'] or [])
    limit = params.get('limit', '')
    limit = min(int(limit) if limit.isdigit() else 20, 100)
    similar_results = check_all_image_urls_for_matches(dataparams['urls'], dataparams['score'],
                                                       dataparams['size'], limit, include_posts,
                                                       sim_clause=dataparams['sim_clause'])
    retdata['similar_results'] = similar_results
    return retdata


def regenerate_post_image_hash():
    post_id = request.values.get('post_id', type=int)
    post = Post.find(post_id) if post_id is not None else None
    retdata = {'error': False, 'post_id': post_id}
    if post is None:
        return set_error(retdata, "Must use a valid post id.")
    delete_image_hash_by_post_id(post.id)
    delete_similarity_matches_by_post_id(post.id)
    generate_post_image_hashes(post)
    generate_similarity_matches(post, singular=True)
    SESSION.commit()
    return retdata


# #### Route functions

@bp.route('/image_hashes/check.json', methods=['GET'])
def check_json():
    return jsonify_data(check(True))


@bp.route('/image_hashes/check', methods=['GET'])
def check_html():
    show_form = request.args.get('show_form', type=eval_bool_string)
    if show_form:
        return render_template("image_hashes/check.html", similar_results=None, form=get_image_hash_form())
    results = check(False)
    formparams = results['data']
    formparams['urls_string'] = '\r\n'.join(formparams['urls'] or [])
    form = get_image_hash_form(**formparams)
    if results['error']:
        flash(results['message'], 'error')
        return render_template("image_hashes/check.html", similar_results=None, form=form)
    similar_results = []
    for i in range(len(results['similar_results'])):
        json_result = results['similar_results'][i]
        if type(json_result) is str:
            flash("%s - %s" % (json_result, results['data']['urls'][i]), 'error')
            continue
        if json_result['error']:
            flash("%s - %s" % (json_result['message'], json_result['download_url']), 'error')
            continue
        post_results = [SimpleNamespace(**post_result) for post_result in json_result['post_results']]
        del json_result['post_results']
        image_match_result = SimpleNamespace(post_results=post_results, **json_result)
        post_ids = [post_result.post_id for post_result in image_match_result.post_results]
        posts = get_posts_by_id(post_ids)
        for post_result in image_match_result.post_results:
            post_result.post = next(filter(lambda x: x.id == post_result.post_id, posts), None)
        similar_results.append(image_match_result)
    return render_template("image_hashes/check.html", similar_results=similar_results, form=form)


@bp.route('/image_hashes/regenerate.json', methods=['POST'])
def regenerate_json():
    return regenerate_post_image_hash()


@bp.route('/image_hashes/regenerate', methods=['POST'])
def regenerate_html():
    results = regenerate_post_image_hash()
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash("Image hash regenerated.")
    return redirect(request.referrer)
