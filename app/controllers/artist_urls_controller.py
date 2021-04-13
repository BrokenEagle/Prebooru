# APP\CONTROLLERS\ILLUSTS.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template

# ## LOCAL IMPORTS
from ..models import ArtistUrl
from .base_controller import GetParamsValue, ProcessRequestValues, ShowJson, IndexJson, SearchFilter, DefaultOrder, Paginate, GetOrAbort


# ## GLOBAL VARIABLES

bp = Blueprint("artist_url", __name__)


# ## FUNCTIONS

# #### Route helpers

def index():
    params = ProcessRequestValues(request.values)
    search = GetParamsValue(params, 'search', True)
    q = ArtistUrl.query
    q = SearchFilter(q, search)
    q = DefaultOrder(q, search)
    return q


# #### Route functions

# ###### SHOW

@bp.route('/artist_urls/<int:id>.json', methods=['GET'])
def show_json(id):
    return ShowJson(ArtistUrl, id)


@bp.route('/artist_urls/<int:id>', methods=['GET'])
def show_html(id):
    artist_url = GetOrAbort(ArtistUrl, id)
    return render_template("artist_urls/show.html", artist_url=artist_url)


# ###### INDEX

@bp.route('/artist_urls.json', methods=['GET'])
def index_json():
    q = index()
    return IndexJson(q, request)


@bp.route('/artist_urls', methods=['GET'])
def index_html():
    q = index()
    artist_urls = Paginate(q, request)
    return render_template("artist_urls/index.html", artist_urls=artist_urls, artist_url=ArtistUrl())
