# APP/CONTROLLERS/SIMILARITY_MATCHES_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, flash, redirect, render_template
from sqlalchemy import and_, or_
from sqlalchemy.orm import selectinload

# ## LOCAL IMPORTS
from .. import SESSION
from ..models import SimilarityMatch
from ..logical.utility import search_url_for
from ..logical.searchable import numeric_filters
from ..logical.database.similarity_match_db import delete_similarity_match,\
    batch_delete_similarity_matches
from .base_controller import get_data_params, get_or_abort, parse_list_type, process_request_values, get_params_value,\
    search_filter, index_json_response, paginate, get_or_error, show_json_response


# ## GLOBAL VARIABLES

bp = Blueprint("similarity_match", __name__)

INDEX_HTML_OPTIONS = (
    selectinload(SimilarityMatch.forward_post).lazyload('*'),
    selectinload(SimilarityMatch.reverse_post).lazyload('*'),
)

NORMAL_ORDER = (SimilarityMatch.forward_id.desc(), SimilarityMatch.reverse_id.desc())

MAX_LIMIT_HTML = 100


# ## FUNCTIONS

def name_params(params, name):
    return dict((name + param[0][4:], param[1]) for param in params.items() if param[0].startswith('post'))


# #### Route auxiliary functions

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = SimilarityMatch.query
    q = search_filter(q, search)
    forward_params = name_params(search, 'forward')
    if len(forward_params):
        reverse_params = name_params(search, 'reverse')
        q = q.filter(or_(
            and_(*numeric_filters(SimilarityMatch, 'forward_id', forward_params)),
            and_(*numeric_filters(SimilarityMatch, 'reverse_id', reverse_params)),
        ))
    if search.get('order') == 'score':
        q.order_by(SimilarityMatch.score.desc(), *NORMAL_ORDER)
    else:
        q = q.order_by(*NORMAL_ORDER)
    return q


# #### Route functions

# ###### SHOW

@bp.route('/similarity_matches/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(SimilarityMatch, id)


@bp.route('/similarity_matches/<int:id>', methods=['GET'])
def show_html(id):
    return redirect(search_url_for('similarity_match.index_html', id=id))


# ###### INDEX

@bp.route('/similarity_matches.json', methods=['GET'])
def index_json():
    q = index()
    return index_json_response(q, request)


@bp.route('/similarity_matches', methods=['GET'])
def index_html():
    q = index()
    q = q.options(INDEX_HTML_OPTIONS)
    similarity_matches = paginate(q, request, MAX_LIMIT_HTML)
    return render_template("similarity_matches/index.html",
                           similarity_matches=similarity_matches,
                           similarity_match=SimilarityMatch())


# ###### DELETE

@bp.route('/similarity_matches', methods=['DELETE'])
def delete_html():
    forward_id = request.values.get('forward_id', type=int)
    reverse_id = request.values.get('reverse_id', type=int)
    if isinstance(forward_id, int) and isinstance(reverse_id, int):
        similarity_match = get_or_abort(SimilarityMatch, forward_id, reverse_id)
        delete_similarity_match(similarity_match)
        flash("Removed from post.")
    else:
        flash("Parameters forward_id and reverse_id not included.", 'error')
    return redirect(request.referrer)


@bp.route('/similarity_matches.json', methods=['DELETE'])
def delete_json():
    forward_id = request.values.get('forward_id', type=int)
    reverse_id = request.values.get('reverse_id', type=int)
    if isinstance(forward_id, int) and isinstance(reverse_id, int):
        element = get_or_error(SimilarityMatch, forward_id, reverse_id)
        if type(element) is dict:
            return element
    else:
        return {'error': True, 'message': "Parameters forward_id and reverse_id not included."}
    delete_similarity_match(element)
    return {'error': False}


# ###### MISC

@bp.route('/similarity_matches/batch_delete', methods=['POST'])
def batch_delete_html():
    dataparams = get_data_params(request, 'similarity_match')
    dataparams['id'] = parse_list_type(dataparams, 'id', int)
    if dataparams['id'] is None or len(dataparams['id']) == 0:
        flash("Must include the IDs of the elements to delete.", 'error')
        return redirect(request.referrer)
    similarity_matches = SimilarityMatch.query.filter(SimilarityMatch.id.in_(dataparams['id'])).all()
    if len(similarity_matches) == 0:
        flash("Found no elements to delete with parameters.")
        return redirect(request.referrer)
    batch_delete_similarity_matches(similarity_matches)
    SESSION.commit()
    flash("Removed elements from post.")
    return redirect(request.referrer)
