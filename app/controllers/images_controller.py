# APP/CONTROLLERS/MEDIA_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, send_from_directory

# ## PACKAGE IMPORTS
from config import MEDIA_DIRECTORY


# ## GLOBAL VARIABLES

bp = Blueprint("media", __name__)


# ## FUNCTIONS

# #### Route functions

# ###### MISC

@bp.route('/media/<path:path>')
def send_file(path):
    return send_from_directory(MEDIA_DIRECTORY, path)
