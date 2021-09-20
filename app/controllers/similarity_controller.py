# APP\CONTROLLERS\SIMILARITY_CONTROLLER.PY

# ## PYTHON IMPORTS
import requests
from types import SimpleNamespace
from flask import Blueprint, request, render_template, flash, redirect
from wtforms import TextAreaField, BooleanField, FloatField
from wtforms.validators import DataRequired


# ## LOCAL IMPORTS
from ..models import Post
from ..database.post_db import GetPostsByID
from ..database.similarity_data_db import delete_similarity_data_by_post_id
from ..database.similarity_pool_db import delete_similarity_pool_by_post_id
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

# #### Route functions

@bp.route('/similarity/check', methods=['GET'])
def check_html():
    params = ProcessRequestValues(request.args)
    params['urls'] = ParseArrayParameter(params, 'urls', 'urls_string', r'\r?\n')
    params['score'] = ParseType(params, 'score', float)
    params['use_original'] = ParseBoolParameter(params, 'use_original')
    if params['urls'] is None or len(params['urls']) is None:
        return render_template("similarity/check.html", similar_results=None, form=GetSimilarityForm(**params))
    try:
        resp = requests.get('http://127.0.0.1:3000/check_similarity.json', params=BuildUrlArgs(params, ['urls', 'score', 'use_original']))
    except requests.exceptions.ReadTimeout:
        abort(502, "Unable to contact similarity server.")
    if resp.status_code != 200:
        abort(503, "Error with similarity server: %d - %s" % (resp.status_code, resp.reason))
    data = resp.json()
    if data['error']:
        abort(504, data['message'])
    similar_results = []
    for json_result in data['similar_results']:
        similarity_result = SimpleNamespace(**json_result)
        similarity_result.post_results = [SimpleNamespace(**post_result) for post_result in similarity_result.post_results]
        post_ids = [post_result.post_id for post_result in similarity_result.post_results]
        posts = GetPostsByID(post_ids)
        for post_result in similarity_result.post_results:
            post_result.post = next(filter(lambda x: x.id == post_result.post_id, posts), None)
        similar_results.append(similarity_result)
    params['url_string'] = '\r\n'.join(params['urls'])
    return render_template("similarity/check.html", similar_results=similar_results, form=GetSimilarityForm(**params))


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
