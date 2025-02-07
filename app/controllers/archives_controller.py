# APP/CONTROLLERS/ARCHIVES_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, url_for, redirect, flash
from sqlalchemy.orm import selectinload

# ## LOCAL IMPORTS
from ..models import Archive
from ..logical.database.archive_db import set_archive_permenant, set_archive_temporary
from ..logical.records.booru_rec import recreate_archived_booru, relink_archived_booru
from ..logical.records.artist_rec import recreate_archived_artist, relink_archived_artist
from ..logical.records.illust_rec import recreate_archived_illust, relink_archived_illust
from ..logical.records.post_rec import recreate_archived_post, relink_archived_post
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_or_abort, index_html_response


# ## GLOBAL VARIABLES

bp = Blueprint("archive", __name__)

RECREATE_ARCHIVE_FUNCS = {
    'booru': recreate_archived_booru,
    'artist': recreate_archived_artist,
    'illust': recreate_archived_illust,
    'post': recreate_archived_post,
}

RELINK_ARCHIVE_FUNCS = {
    'booru': relink_archived_booru,
    'artist': relink_archived_artist,
    'illust': relink_archived_illust,
    'post': relink_archived_post,
}

# #### Load options

LOAD_OPTIONS = (
    selectinload(Archive.post_data),
    selectinload(Archive.illust_data),
    selectinload(Archive.artist_data),
    selectinload(Archive.booru_data),
)


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
    return show_json_response(Archive, id, options=LOAD_OPTIONS)


@bp.route('/archives/<int:id>', methods=['GET'])
def show_html(id):
    archive = get_or_abort(Archive, id, options=LOAD_OPTIONS)
    return render_template("archives/show.html", archive=archive)


# ###### INDEX

@bp.route('/archives.json', methods=['GET'])
def index_json():
    q = index()
    q = q.options(LOAD_OPTIONS)
    return index_json_response(q, request)


@bp.route('/archives', methods=['GET'])
def index_html():
    q = index()
    q = q.options(LOAD_OPTIONS)
    page = paginate(q, request)
    return index_html_response(page, 'archive', 'archives')


# ###### MISC

@bp.route('/archives/<int:id>/reinstantiate', methods=['POST'])
def reinstantiate_item_html(id):
    archive = get_or_abort(Archive, id)
    retdata = RECREATE_ARCHIVE_FUNCS[archive.type.name](archive)
    if retdata['error']:
        flash(retdata['message'], 'error')
    else:
        flash(archive.type.name.title() + " recreated.")
    if 'item' not in retdata:
        return redirect(request.referrer)
    return redirect(url_for(archive.type.name + '.show_html', id=retdata['item']['id']))


@bp.route('/archives/<int:id>/relink', methods=['POST'])
def relink_item_html(id):
    archive = get_or_abort(Archive, id)
    retdata = RELINK_ARCHIVE_FUNCS[archive.type.name](archive)
    if retdata['error']:
        flash(retdata['message'], 'error')
    else:
        flash(archive.type.name.title() + " relinked.")
    if 'item' not in retdata:
        return redirect(request.referrer)
    return redirect(url_for(archive.type.name + '.show_html', id=retdata['item']['id']))


@bp.route('/archives/<int:id>/set_permenant', methods=['POST'])
def set_permenant_html(id):
    archive = get_or_abort(Archive, id)
    set_archive_permenant(archive)
    return redirect(request.referrer)


@bp.route('/archives/<int:id>/set_temporary', methods=['POST'])
def set_temporary_html(id):
    archive = get_or_abort(Archive, id)
    set_archive_temporary(archive, 30, commit=True)  # Eventually add model specific delay times here
    return redirect(request.referrer)
