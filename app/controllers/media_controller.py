# APP/CONTROLLERS/MEDIA_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, send_from_directory

# ## PACKAGE IMPORTS
from config import MEDIA_DIRECTORY, ALTERNATE_MEDIA_DIRECTORY


# ## GLOBAL VARIABLES

bp = Blueprint("media", __name__)

DIRECTORIES = {
    'main': MEDIA_DIRECTORY,
    'alternate': ALTERNATE_MEDIA_DIRECTORY,
}


# ## FUNCTIONS

# #### Route functions

# ###### MISC

@bp.route('/media/<subtype>/<path:path>')
def send_file(subtype, path):
    directory = DIRECTORIES[subtype]
    return send_from_directory(directory, path)


@bp.after_request
def add_header(response):
    response.cache_control.max_age = 3600
    response.cache_control.no_cache = None
    return response
