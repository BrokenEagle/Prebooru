# APP/CONTROLLERS/SIMILARITY_CONTROLLER.PY

# ## PYTHON IMPORTS
from types import SimpleNamespace

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, flash, redirect
from wtforms import TextAreaField, BooleanField, FloatField, SelectField
from wtforms.validators import DataRequired


# ## LOCAL IMPORTS
from ..models import Post
from ..logical.utility import set_error
from ..logical.database.post_db import get_posts_by_id
from ..logical.database.similarity_data_db import delete_similarity_data_by_post_id
from ..logical.database.similarity_pool_db import delete_similarity_pool_by_post_id
from ..logical.similarity.check_image import check_all_image_urls_similarity
from ..logical.similarity.generate_data import generate_post_similarity
from ..logical.similarity.populate_pools import populate_similarity_pools
from .base_controller import process_request_values, CustomNameForm, parse_type, parse_bool_parameter,\
    parse_string_list, nullify_blanks, set_default, check_param_requirements, eval_bool_string


# ## GLOBAL VARIABLES

bp = Blueprint("similarity", __name__)


# #### Forms

def get_similarity_form(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class SimilarityForm(CustomNameForm):
        urls_string = TextAreaField('URLs', id='similarity-urls', custom_name='urls_string',
                                    description="Separated by carriage returns.", validators=[DataRequired()])
        score = FloatField('Score', id='similarity-score',
                           description="Lowest score of results to return. Default is 90.0.")
        use_original = BooleanField('Use Original', id='similarity-use-original',
                                    description="Uses the original image URL instead of the small version.")
        sim_clause = SelectField('Similarity clause',
                                 choices=[("", ""), ('chunk', 'Chunk'), ('cross0', 'Cross #0'), ('cross0', 'Cross #1'),
                                          ('cross2', 'Cross #2'), ('all', 'All')],
                                 id='similarity-sim-clause')
    return SimilarityForm(**kwargs)


# ## FUNCTIONS

# #### Helper functions

def convert_data_params(dataparams):
    params = get_similarity_form(**dataparams).data
    if 'urls' in dataparams:
        params['urls'] = dataparams['urls']
    elif 'urls_string' in dataparams:
        params['urls'] = parse_string_list(dataparams, 'urls_string', r'\r?\n')
    else:
        params['urls'] = None
    params['use_original'] = parse_bool_parameter(dataparams, 'use_original')
    params['score'] = parse_type(dataparams, 'score', float)
    params = nullify_blanks(params)
    set_default(params, 'score', 90.0)
    set_default(params, 'use_original', False)
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
    dataparams['url_string'] = '\r\n'.join(dataparams['urls'])
    similar_results = check_all_image_urls_similarity(dataparams['urls'], dataparams['score'],
                                                      dataparams['use_original'], include_posts,
                                                      sim_clause=dataparams['sim_clause'])
    retdata['similar_results'] = similar_results
    return retdata


def generate_similarity():
    post_id = request.values.get('post_id', type=int)
    post = Post.find(post_id) if post_id is not None else None
    retdata = {'error': False, 'post_id': post_id}
    if post is None:
        return set_error(retdata, "Must use a valid post id.")
    delete_similarity_data_by_post_id(post.id)
    delete_similarity_pool_by_post_id(post.id)
    generate_post_similarity(post)
    populate_similarity_pools(post)
    return retdata


# #### Route functions

@bp.route('/similarity/check.json', methods=['GET'])
def check_json():
    return check(True)


@bp.route('/similarity/check', methods=['GET'])
def check_html():
    show_form = request.args.get('show_form', type=eval_bool_string)
    if show_form:
        return render_template("similarity/check.html", similar_results=None, form=get_similarity_form())
    results = check(False)
    form = get_similarity_form(**results['data'])
    if results['error']:
        flash(results['message'], 'error')
        return render_template("similarity/check.html", similar_results=None, form=form)
    similar_results = []
    for i in range(len(results['similar_results'])):
        json_result = results['similar_results'][i]
        if type(json_result) is str:
            flash("%s - %s" % (json_result, results['data']['urls'][i]), 'error')
            continue
        post_results = [SimpleNamespace(**post_result) for post_result in json_result['post_results']]
        del json_result['post_results']
        similarity_result = SimpleNamespace(post_results=post_results, **json_result)
        post_ids = [post_result.post_id for post_result in similarity_result.post_results]
        posts = get_posts_by_id(post_ids)
        for post_result in similarity_result.post_results:
            post_result.post = next(filter(lambda x: x.id == post_result.post_id, posts), None)
        similar_results.append(similarity_result)
    return render_template("similarity/check.html", similar_results=similar_results, form=form)


@bp.route('/similarity/regenerate.json', methods=['POST'])
def regenerate_json():
    return generate_similarity()


@bp.route('/similarity/regenerate', methods=['POST'])
def regenerate_html():
    results = generate_similarity()
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash("Similarity regenerated.")
    return redirect(request.referrer)
