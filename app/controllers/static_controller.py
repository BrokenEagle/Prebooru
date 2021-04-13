# APP\CONTROLLERS\STATIC_CONTROLLER.PY

# ## PYTHON IMPORTS
from flask import Blueprint, render_template


# ##GLOBAL VARIABLES

bp = Blueprint("static", __name__)


# ##FUNCTIONS

@bp.route('/static/site_map', methods=['GET'])
def site_map_html():
    return render_template("static/site_map.html")


@bp.route('/static/bookmarklet_info', methods=['GET'])
def bookmarklet_info_html():
    return render_template("static/bookmarklet_info.html")
