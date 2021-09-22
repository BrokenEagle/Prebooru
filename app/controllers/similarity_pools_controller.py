# APP\CONTROLLERS\SIMILARITY_POOLS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template

# ## LOCAL IMPORTS
from ..models import SimilarityPool, Post
from .base_controller import show_json, get_page, get_limit, get_or_abort


# ## GLOBAL VARIABLES

bp = Blueprint("similarity_pool", __name__)


# ## FUNCTIONS

# #### Route functions

@bp.route('/similarity_pools/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json(SimilarityPool, id)


@bp.route('/similarity_pools/<int:id>', methods=['GET'])
def show_html(id):
    similarity_pool = get_or_abort(SimilarityPool, id)
    elements = similarity_pool.element_paginate(page=get_page(request), per_page=get_limit(request))
    return render_template("similarity_pools/show.html", similarity_pool=similarity_pool, elements=elements)
