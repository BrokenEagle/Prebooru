# APP/CONTROLLERS/ARCHIVE_DATA_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, url_for, redirect, flash

# ## LOCAL IMPORTS
from ..models import ArchiveData
from ..logical.database.archive_data_db import set_archive_data_permenant, set_archive_data_temporary
from ..logical.records.archive_data_rec import relink_archive_data_item, reinstantiate_archive_data_item
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_or_abort


# ## GLOBAL VARIABLES

bp = Blueprint("archive_data", __name__)


# ## FUNCTIONS

# #### Route auxiliary functions

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = ArchiveData.query
    q = search_filter(q, search)
    q = default_order(q, search)
    return q


# #### Route functions

# ###### SHOW

@bp.route('/archive_data/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(ArchiveData, id)


@bp.route('/archive_data/<int:id>', methods=['GET'])
def show_html(id):
    archive_data = get_or_abort(ArchiveData, id)
    return render_template("archive_data/show.html", archive_datum=archive_data)


# ###### INDEX

@bp.route('/archive_data.json', methods=['GET'])
def index_json():
    q = index()
    return index_json_response(q, request)


@bp.route('/archive_data', methods=['GET'])
def index_html():
    q = index()
    archive_data = paginate(q, request)
    return render_template("archive_data/index.html", archive_data=archive_data, archive_datum=ArchiveData())


# ###### MISC

@bp.route('/archive_data/<int:id>/reinstantiate', methods=['POST'])
def reinstantiate_item_html(id):
    archive_data = get_or_abort(ArchiveData, id)
    retdata = reinstantiate_archive_data_item(archive_data)
    if retdata['error']:
        flash(retdata['message'], 'error')
    else:
        flash(archive_data.type.title() + " recreated.")
    if 'item' not in retdata:
        return redirect(request.referrer)
    return redirect(url_for(archive_data.type + '.show_html', id=retdata['item']['id']))


@bp.route('/archive_data/<int:id>/relink', methods=['POST'])
def relink_item_html(id):
    archive_data = get_or_abort(ArchiveData, id)
    retdata = relink_archive_data_item(archive_data)
    if retdata['error']:
        flash(retdata['message'], 'error')
    else:
        flash(archive_data.type.title() + " relinked.")
    if 'item' not in retdata:
        return redirect(request.referrer)
    return redirect(url_for(archive_data.type + '.show_html', id=retdata['item']['id']))


@bp.route('/archive_data/<int:id>/set_permenant', methods=['POST'])
def set_permenant_html(id):
    archive_data = get_or_abort(ArchiveData, id)
    set_archive_data_permenant(archive_data)
    return redirect(request.referrer)


@bp.route('/archive_data/<int:id>/set_temporary', methods=['POST'])
def set_temporary_html(id):
    archive_data = get_or_abort(ArchiveData, id)
    set_archive_data_temporary(archive_data, 30)  # Eventually add model specific delay times here
    return redirect(request.referrer)
