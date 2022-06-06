# APP/CONTROLLERS/SUBSCRIPTION_POOL_ELEMENTS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, flash, redirect
from sqlalchemy import or_
from sqlalchemy.orm import selectinload

# ## PACKAGE IMPORTS
from utility.data import eval_bool_string

# ## LOCAL IMPORTS
from ..models import SubscriptionPoolElement, IllustUrl, Illust
from ..logical.utility import search_url_for
from ..logical.database.subscription_pool_element_db import get_elements_by_id, update_subscription_pool_element_keep,\
    batch_update_subscription_pool_element_keep
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_or_abort, get_or_error, strip_whitespace


# ## GLOBAL VARIABLES

bp = Blueprint("subscription_pool_element", __name__)

# #### Load options

INDEX_HTML_OPTIONS = (
    selectinload(SubscriptionPoolElement.illust_url).selectinload(IllustUrl.illust).selectinload(Illust.urls).lazyload('*'),
    selectinload(SubscriptionPoolElement.post).lazyload('*'),
    selectinload(SubscriptionPoolElement.errors),
)

MAX_LIMIT_HTML = 100


# ## FUNCTIONS

# #### Route auxiliary functions

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = SubscriptionPoolElement.query
    q = search_filter(q, search)
    if search.get('order') == 'expires':
        q = q.filter(SubscriptionPoolElement.expires.is_not(None)).order_by(SubscriptionPoolElement.expires.asc())
    elif search.get('order') == 'site':
        q = q.unique_join(IllustUrl).unique_join(Illust).order_by(Illust.site_illust_id.desc())
    else:
        q = default_order(q, search)
    return q


# #### Route functions

# ###### SHOW

@bp.route('/subscription_pool_elements/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(SubscriptionPoolElement, id)


@bp.route('/subscription_pool_elements/<int:id>', methods=['GET'])
def show_html(id):
    return redirect(search_url_for('subscription_pool_element.index_html', base_args={'type': 'all'}, id=id))


@bp.route('/subscription_pool_elements/<int:id>/preview.json', methods=['GET'])
def preview_json(id):
    subscription_pool_element = get_or_abort(SubscriptionPoolElement, id)
    html = render_template("subscription_pool_elements/_element_preview.html", element=subscription_pool_element)
    return {'item': subscription_pool_element.to_json(), 'html': strip_whitespace(html)}


# ###### INDEX

@bp.route('/subscription_pool_elements.json', methods=['GET'])
def index_json():
    q = index()
    return index_json_response(q, request)


@bp.route('/subscription_pool_elements', methods=['GET'])
def index_html():
    q = index()
    element_type = request.args.get('type')
    if request.args.get('search[keep]') is None:
        if element_type != 'all':
            q = q.filter(SubscriptionPoolElement.post_id.__ne__(None))
        if element_type in ['yes', 'no', 'maybe']:
            q = q.filter(SubscriptionPoolElement.keep == element_type)
        elif element_type == 'unsure' or element_type is None:
            q = q.filter(SubscriptionPoolElement.keep.is_(None))
    q = q.options(INDEX_HTML_OPTIONS)
    subscription_pool_elements = paginate(q, request, MAX_LIMIT_HTML)
    return render_template("subscription_pool_elements/index.html",
                           subscription_pool_elements=subscription_pool_elements,
                           subscription_pool_element=SubscriptionPoolElement())


# ###### Misc

@bp.route('/subscription_pool_elements/keep', methods=['POST'])
def batch_keep_html():
    params = process_request_values(request.values)
    data_params = get_params_value(params, 'subscription_pool_element', True)
    if 'keep' not in data_params or data_params['keep'] not in ['yes', 'no', 'maybe']:
        flash("Invalid or missing keep value.", 'error')
        return redirect(request.referrer)
    if 'id' not in data_params or not isinstance(data_params['id'], list):
        flash("Invalid or missing id values.", 'error')
        return redirect(request.referrer)
    id_list = [int(id) for id in data_params['id']]
    elements = get_elements_by_id(id_list)
    missing_ids = list(set(id_list).difference([element.id for element in elements]))
    if len(missing_ids) > 0:
        flash(f"Unable to find elements: {repr(missing_ids)}")
    batch_update_subscription_pool_element_keep(elements, data_params['keep'])
    return redirect(request.referrer)


@bp.route('/subscription_pool_elements/<int:id>/keep', methods=['POST'])
def keep_html(id):
    element = get_or_abort(SubscriptionPoolElement, id)
    value = request.args.get('keep')
    if value is None:
        flash("Keep argument not found.", 'error')
    else:
        flash("Element updated.")
        update_subscription_pool_element_keep(element, value)
    return redirect(request.referrer)


@bp.route('/subscription_pool_elements/<int:id>/keep.json', methods=['POST'])
def keep_json(id):
    element = get_or_error(SubscriptionPoolElement, id)
    if isinstance(element, str):
        return element
    messages = []
    value = request.args.get('keep')
    if value is None:
        messages.append("Keep argument not found.")
    has_preview = request.args.get('preview', type=eval_bool_string)
    if has_preview is None:
        messages.append("Preview argument not found.")
    if len(messages) > 0:
        return {'error': True, 'message': '<br>'.join(messages)}
    update_subscription_pool_element_keep(element, value)
    html = render_template("subscription_pool_elements/_element_preview.html", element=element) if has_preview else render_template("subscription_pool_elements/_element_info.html", element=element)
    return {'error': False, 'item': element.to_json(), 'html': strip_whitespace(html)}
