# APP\CONTROLLERS\IMAGES_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, send_from_directory

# ## LOCAL IMPORTS
from ..config import IMAGE_DIRECTORY

# ## GLOBAL VARIABLES

bp = Blueprint("images", __name__)


# ## FUNCTIONS

# #### Route functions

# ###### MISC

@bp.route('/images/<path:path>')
def send_file(path):
    return send_from_directory(IMAGE_DIRECTORY, path)
