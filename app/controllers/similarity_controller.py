# APP\CONTROLLERS\SIMILARITY_CONTROLLER.PY

# ## PYTHON IMPORTS
from types import SimpleNamespace
from flask import Blueprint, request, render_template, flash, redirect
from wtforms import TextAreaField, BooleanField, FloatField
from wtforms.validators import DataRequired


# ## LOCAL IMPORTS
from ..models import Post
from ..database.post_db import GetPostsByID
from ..database.similarity_data_db import delete_similarity_data_by_post_id
from ..database.similarity_pool_db import delete_similarity_pool_by_post_id
from ..logical.similarity.check_image import check_all_image_urls_similarity
from ..logical.similarity.generate_data import generate_post_similarity
from ..logical.similarity.populate_pools import populate_similarity_pools
from .base_controller import ProcessRequestValues, CustomNameForm, ParseType, ParseBoolParameter, ParseStringList, NullifyBlanks,\
    SetDefault, CheckParamRequirements, SetError


# ## GLOBAL VARIABLES

bp = Blueprint("similarity", __name__)


# #### Forms

def GetSimilarityForm(**kwargs):
    # Class has to be declared every time because the custom_name isn't persistent accross page refreshes
    class SimilarityForm(CustomNameForm):
        urls_string = TextAreaField('URLs', id='similarity-urls', custom_name='urls_string', description="Separated by carriage returns.", validators=[DataRequired()])
        score = FloatField('Score', id='similarity-score', description="Lowest score of results to return. Default is 90.0.")
        use_original = BooleanField('Use Original', id='similarity-use-original', description="Uses the original image URL instead of the small version.")
    return SimilarityForm(**kwargs)


# ## FUNCTIONS

# #### Helper functions

def convert_data_params(dataparams):
    params = GetSimilarityForm(**dataparams).data
    if 'urls' in dataparams:
        params['urls'] = dataparams['urls']
    elif 'urls_string' in dataparams:
        params['urls'] = ParseStringList(dataparams, 'urls_string', r'\r?\n')
    params['use_original'] = ParseBoolParameter(dataparams, 'use_original')
    params['score'] = ParseType(dataparams, 'score', float)
    params = NullifyBlanks(params)
    SetDefault(params, 'score', 90.0)
    SetDefault(params, 'use_original', False)
    return params


# #### Route auxiliary functions

def check(include_posts):
    params = ProcessRequestValues(request.args)
    dataparams = convert_data_params(params)
    retdata = {'error': False, 'data': dataparams, 'params': params}
    errors = CheckParamRequirements(dataparams, ['urls'])
    if len(errors) > 0:
        return SetError(retdata, '\n'.join(errors))
    dataparams['url_string'] = '\r\n'.join(dataparams['urls'])
    similar_results = check_all_image_urls_similarity(dataparams['urls'], dataparams['score'], dataparams['use_original'], include_posts)
    if type(similar_results) is str:
        return SetError(retdata, similar_results)
    retdata['similar_results'] = similar_results
    return retdata


def generate_similarity():
    post_id = request.values.get('post_id', type=int)
    post = Post.find(post_id) if post_id is not None else None
    retdata = {'error': False, 'post_id': post_id}
    if post is None:
        return SetError(retdata, "Must use a valid post id.")
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
    results = check(False)
    form = GetSimilarityForm(**results['data'])
    if results['error']:
        flash(results['message'], 'error')
        return render_template("similarity/check.html", similar_results=None, form=form)
    similar_results = []
    for json_result in results['similar_results']:
        similarity_result = SimpleNamespace(**json_result)
        similarity_result.post_results = [SimpleNamespace(**post_result) for post_result in similarity_result.post_results]
        post_ids = [post_result.post_id for post_result in similarity_result.post_results]
        posts = GetPostsByID(post_ids)
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
