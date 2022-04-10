# APP/CONTROLLERS/SUBSCRIPTION_POOL_ELEMENTS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template
from sqlalchemy import or_
from sqlalchemy.orm import selectinload

# ## LOCAL IMPORTS
from ..models import SubscriptionPoolElement
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_or_abort, get_or_error


# ## GLOBAL VARIABLES

bp = Blueprint("subscription_pool_element", __name__)

# #### Load options

INDEX_HTML_OPTIONS = (
    selectinload(SubscriptionPoolElement.illust_url).lazyload('*'),
)


# ## FUNCTIONS

# #### Route auxiliary functions

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = SubscriptionPoolElement.query
    q = search_filter(q, search)
    if 'order' in search and search['order'] == 'expires':
        q = q.order_by(SubscriptionPoolElement.expires.asc())
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
    subscription_pool_element = get_or_abort(SubscriptionPoolElement, id)
    return render_template("subscription_pool_elements/show.html", subscription_pool_element=subscription_pool_element)


# ###### INDEX

@bp.route('/subscription_pool_elements.json', methods=['GET'])
def index_json():
    q = index()
    return index_json_response(q, request)


@bp.route('/subscription_pool_elements', methods=['GET'])
def index_html():
    q = index()
    element_type = request.args.get('type')
    if element_type != 'all':
        q = q.filter(SubscriptionPoolElement.post_id.__ne__(None))
    if request.args.get('search[keep]') is None:
        if element_type in ['yes', 'no']:
            q = q.filter(SubscriptionPoolElement.keep == element_type)
        elif element_type == 'unsure' or element_type is None:
            q = q.filter(or_(SubscriptionPoolElement.keep == 'maybe', SubscriptionPoolElement.keep.__eq__(None)))
    q = q.options(INDEX_HTML_OPTIONS)
    subscription_pool_elements = paginate(q, request)
    return render_template("subscription_pool_elements/index.html",
                           subscription_pool_elements=subscription_pool_elements,
                           subscription_pool_element=SubscriptionPoolElement())
