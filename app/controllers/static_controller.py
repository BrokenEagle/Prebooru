# APP/CONTROLLERS/STATIC_CONTROLLER.PY

# ## PYTHON IMPORTS
import os

# ## EXTERNAL IMPORTS
from flask import Blueprint, render_template, send_from_directory

# ## LOCAL IMPORTS
from .. import PREBOORU_APP


# ## GLOBAL VARIABLES

bp = Blueprint("static", __name__)

STATIC_PATH = os.path.join(PREBOORU_APP.root_path, 'app', 'static')


# ## FUNCTIONS

@PREBOORU_APP.route('/favicon.ico')
def favicon():
    return send_from_directory(STATIC_PATH, 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@bp.route('/static/site_map', methods=['GET'])
def site_map_html():
    return render_template("static/site_map.html")


@bp.route('/static/bookmarklet_info', methods=['GET'])
def bookmarklet_info_html():
    return render_template("static/bookmarklet_info.html")
