# APP\CONTROLLERS\POOL_ELEMENTS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, flash, redirect


# ## LOCAL IMPORTS
from ..models import SimilarityPoolElement
from ..logical.database.similarity_pool_element_db import delete_similarity_pool_element, batch_delete_similarity_pool_element
from .base_controller import get_data_params, get_or_abort, parse_list_type


# ## GLOBAL VARIABLES

bp = Blueprint("similarity_pool_element", __name__)


# ## FUNCTIONS

# #### Route functions

# ###### DELETE

@bp.route('/similarity_pool_elements/<int:id>', methods=['DELETE'])
def delete_html(id):
    similarity_pool_element = get_or_abort(SimilarityPoolElement, id)
    delete_similarity_pool_element(similarity_pool_element)
    flash("Removed from post.")
    return redirect(request.referrer)


# ###### MISC

@bp.route('/similarity_pool_elements/batch_delete', methods=['POST'])
def batch_delete_html():
    dataparams = get_data_params(request, 'similarity_pool_element')
    dataparams['id'] = parse_list_type(dataparams, 'id', int)
    if dataparams['id'] is None or len(dataparams['id']) == 0:
        flash("Must include the IDs of the elements to delete.", 'error')
        return redirect(request.referrer)
    similarity_pool_elements = SimilarityPoolElement.query.filter(SimilarityPoolElement.id.in_(dataparams['id'])).all()
    if len(similarity_pool_elements) == 0:
        flash("Found no elements to delete with parameters.")
        return redirect(request.referrer)
    batch_delete_similarity_pool_element(similarity_pool_elements)
    flash("Removed elements from post.")
    return redirect(request.referrer)
