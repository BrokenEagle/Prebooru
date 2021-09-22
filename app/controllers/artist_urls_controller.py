# APP\CONTROLLERS\ILLUSTS.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template

# ## LOCAL IMPORTS
from ..models import ArtistUrl
from .base_controller import get_params_value, process_request_values, show_json, index_json, search_filter, default_order, paginate, get_or_abort


# ## GLOBAL VARIABLES

bp = Blueprint("artist_url", __name__)


# ## FUNCTIONS

# #### Route helpers

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = ArtistUrl.query
    q = search_filter(q, search)
    q = default_order(q, search)
    return q


# #### Route functions

# ###### SHOW

@bp.route('/artist_urls/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json(ArtistUrl, id)


@bp.route('/artist_urls/<int:id>', methods=['GET'])
def show_html(id):
    artist_url = get_or_abort(ArtistUrl, id)
    return render_template("artist_urls/show.html", artist_url=artist_url)


# ###### INDEX

@bp.route('/artist_urls.json', methods=['GET'])
def index_json():
    q = index()
    return index_json(q, request)


@bp.route('/artist_urls', methods=['GET'])
def index_html():
    q = index()
    artist_urls = paginate(q, request)
    return render_template("artist_urls/index.html", artist_urls=artist_urls, artist_url=ArtistUrl())
