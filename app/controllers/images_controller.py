# APP\CONTROLLERS\ILLUSTS.PY

# ## PYTHON IMPORTS
from flask import Blueprint, request, render_template, send_from_directory

# ## LOCAL IMPORTS
from ..models import ArtistUrl
from .base_controller import GetParamsValue, ProcessRequestValues, ShowJson, IndexJson, SearchFilter, DefaultOrder, Paginate, GetOrAbort
from app.storage import IMAGE_DIRECTORY

# ## GLOBAL VARIABLES
from ..storage import IMAGE_DIRECTORY

bp = Blueprint("images", __name__)


# ## FUNCTIONS

# #### Route helpers

# #### Route functions

# ###### SHOW

@bp.route('/images/<path:path>')
def send_file(path):
    return send_from_directory(IMAGE_DIRECTORY, path)

# ###### INDEX
