# APP\CONTROLLERS\SIMILARITY_POOLS_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template

# ## LOCAL IMPORTS
from ..similarity import SimilarityPool
from ..models import Post
from .base_controller import ShowJson, GetPage, GetLimit, GetOrAbort


# ## GLOBAL VARIABLES

bp = Blueprint("similarity_pool", __name__)


# ## FUNCTIONS

# #### Route functions

@bp.route('/similarity_pools/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(SimilarityPool, id)


@bp.route('/similarity_pools/<int:id>', methods=['GET'])
def show_html(id):
    similarity_pool = GetOrAbort(SimilarityPool, id)
    post = Post.find(similarity_pool.post_id)
    elements = similarity_pool.element_paginate(page=GetPage(request), per_page=GetLimit(request))
    return render_template("similarity_pools/show.html", similarity_pool=similarity_pool, post=post, elements=elements)
