# APP/CONTROLLERS/ARCHIVES_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, url_for, redirect, flash

# ## LOCAL IMPORTS
from ..models import Archive
from ..logical.database.archive_db import set_archive_permenant, set_archive_temporary
from ..logical.records.archive_rec import relink_archive_item, reinstantiate_archive_item
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_or_abort


# ## GLOBAL VARIABLES

bp = Blueprint("archive", __name__)


# ## FUNCTIONS

# #### Route auxiliary functions

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = Archive.query
    q = search_filter(q, search)
    q = default_order(q, search)
    return q


# #### Route functions

# ###### SHOW

@bp.route('/archives/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(Archive, id)


@bp.route('/archives/<int:id>', methods=['GET'])
def show_html(id):
    archive = get_or_abort(Archive, id)
    return render_template("archives/show.html", archive=archive)


# ###### INDEX

@bp.route('/archives.json', methods=['GET'])
def index_json():
    q = index()
    return index_json_response(q, request)


@bp.route('/archives', methods=['GET'])
def index_html():
    q = index()
    archives = paginate(q, request)
    return render_template("archives/index.html", archives=archives, archive=Archive())


# ###### MISC

@bp.route('/archives/<int:id>/reinstantiate', methods=['POST'])
def reinstantiate_item_html(id):
    archive = get_or_abort(Archive, id)
    retdata = reinstantiate_archive_item(archive)
    if retdata['error']:
        flash(retdata['message'], 'error')
    else:
        flash(archive.type.title() + " recreated.")
    if 'item' not in retdata:
        return redirect(request.referrer)
    return redirect(url_for(archive.type + '.show_html', id=retdata['item']['id']))


@bp.route('/archives/<int:id>/relink', methods=['POST'])
def relink_item_html(id):
    archive = get_or_abort(Archive, id)
    retdata = relink_archive_item(archive)
    if retdata['error']:
        flash(retdata['message'], 'error')
    else:
        flash(archive.type.title() + " relinked.")
    if 'item' not in retdata:
        return redirect(request.referrer)
    return redirect(url_for(archive.type + '.show_html', id=retdata['item']['id']))


@bp.route('/archives/<int:id>/set_permenant', methods=['POST'])
def set_permenant_html(id):
    archive = get_or_abort(Archive, id)
    set_archive_permenant(archive)
    return redirect(request.referrer)


@bp.route('/archives/<int:id>/set_temporary', methods=['POST'])
def set_temporary_html(id):
    archive = get_or_abort(Archive, id)
    set_archive_temporary(archive, 30)  # Eventually add model specific delay times here
    return redirect(request.referrer)
