# APP\CONTROLLERS\POOL_ELEMENTS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, flash, redirect


# ## LOCAL IMPORTS
from ..models import SimilarityPoolElement
from ..database.similarity_pool_element_db import DeleteSimilarityPoolElement, BatchDeleteSimilarityPoolElement
from .base_controller import GetDataParams, GetOrAbort, ParseListType


# ## GLOBAL VARIABLES

bp = Blueprint("similarity_pool_element", __name__)


# ## FUNCTIONS

# #### Route functions

# ###### DELETE

@bp.route('/similarity_pool_elements/<int:id>', methods=['DELETE'])
def delete_html(id):
    similarity_pool_element = GetOrAbort(SimilarityPoolElement, id)
    DeleteSimilarityPoolElement(similarity_pool_element)
    flash("Removed from post.")
    return redirect(request.referrer)


# ###### MISC

@bp.route('/similarity_pool_elements/batch_delete', methods=['POST'])
def batch_delete_html():
    dataparams = GetDataParams(request, 'similarity_pool_element')
    dataparams['id'] = ParseListType(dataparams, 'id', int)
    if dataparams['id'] is None or len(dataparams['id']) == 0:
        flash("Must include the IDs of the elements to delete.", 'error')
        return redirect(request.referrer)
    similarity_pool_elements = SimilarityPoolElement.query.filter(SimilarityPoolElement.id.in_(dataparams['id'])).all()
    if len(similarity_pool_elements) == 0:
        flash("Found no elements to delete with parameters.")
        return redirect(request.referrer)
    BatchDeleteSimilarityPoolElement(similarity_pool_elements)
    flash("Removed elements from post.")
    return redirect(request.referrer)
