# APP/CONTROLLERS/SUBSCRIPTION_ELEMENTS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, flash, redirect, url_for
from sqlalchemy.orm import selectinload

# ## PACKAGE IMPORTS
from utility.data import eval_bool_string

# ## LOCAL IMPORTS
from ..models import SubscriptionElement, IllustUrl, Illust
from ..logical.utility import search_url_for
from ..logical.database.subscription_element_db import get_elements_by_id, update_subscription_element_keep,\
    batch_update_subscription_element_keep
from ..logical.database.post_db import get_posts_by_md5s, get_post_by_md5
from ..logical.database.archive_db import get_archive_posts_by_md5s, get_archive
from ..logical.records.subscription_rec import redownload_element, reinstantiate_element, relink_element
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_or_abort, get_or_error, strip_whitespace, get_page,\
    render_template_ws


# ## GLOBAL VARIABLES

bp = Blueprint("subscription_element", __name__)

# #### Load options

INDEX_HTML_OPTIONS = (
    selectinload(SubscriptionElement.illust_url).selectinload(IllustUrl.illust)
                                                .selectinload(Illust.urls)
                                                .lazyload('*'),
    selectinload(SubscriptionElement.post).lazyload('*'),
    selectinload(SubscriptionElement.errors),
)

MAX_LIMIT_HTML = 100


# ## FUNCTIONS

# #### Route auxiliary functions

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    q = SubscriptionElement.query
    q = search_filter(q, search)
    if search.get('order') == 'expires':
        q = q.filter(SubscriptionElement.expires.is_not(None)).order_by(SubscriptionElement.expires.asc())
    elif search.get('order') == 'site':
        q = q.unique_join(IllustUrl).unique_join(Illust).order_by(Illust.site_illust_id.desc())
    else:
        q = default_order(q, search)
    return q


# #### Route functions

# ###### SHOW

@bp.route('/subscription_elements/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(SubscriptionElement, id)


@bp.route('/subscription_elements/<int:id>', methods=['GET'])
def show_html(id):
    return redirect(search_url_for('subscription_element.index_html', base_args={'type': 'all'}, id=id))


@bp.route('/subscription_elements/<int:id>/preview.json', methods=['GET'])
def preview_json(id):
    subscription_element = get_or_abort(SubscriptionElement, id)
    html = render_template_ws("subscription_elements/_element_preview.html", element=subscription_element)
    return {'item': subscription_element.to_json(), 'html': html}


# ###### INDEX

@bp.route('/subscription_elements.json', methods=['GET'])
def index_json():
    q = index()
    return index_json_response(q, request)


@bp.route('/subscription_elements', methods=['GET'])
def index_html():
    q = index()
    element_type = request.args.get('type')
    if request.args.get('search[keep]') is None:
        if element_type != 'all':
            q = q.filter(SubscriptionElement.post_id.__ne__(None))
        if element_type in ['yes', 'no', 'maybe', 'archive']:
            q = q.filter(SubscriptionElement.keep == element_type)
        elif element_type == 'undecided' or element_type is None:
            q = q.filter(SubscriptionElement.keep.is_(None))
    q = q.options(INDEX_HTML_OPTIONS)
    elements = paginate(q, request, MAX_LIMIT_HTML)
    page = get_page(request)
    if page is not None and page != 1 and len(elements.items) == 0\
            and page > elements.pages:
        return redirect(url_for('subscription_element.index_html', page=elements.pages,
                                **{k: v for (k, v) in request.args.items() if k != 'page'}))
    missing_md5s = set(element.md5 for element in elements.items
                       if element.post is None and element.status.name in ['unlinked', 'duplicate'])
    missing_posts = get_posts_by_md5s(list(missing_md5s)) if len(missing_md5s) else []
    archive_md5s = set(element.md5 for element in elements.items if element.status.name == 'archived')
    archives = get_archive_posts_by_md5s(list(archive_md5s)) if len(archive_md5s) else []
    for item in elements.items:
        post_match = None
        if item.md5 in missing_md5s:
            post_match = next((post for post in missing_posts if post.md5 == item.md5), None)
        setattr(item, 'post_match', post_match)
        archive_match = None
        if item.md5 in archive_md5s:
            archive_match = next((archive for archive in archives if archive.key == item.md5), None)
        setattr(item, 'archive_match', archive_match)
    return render_template_ws("subscription_elements/index.html",
                              subscription_elements=elements,
                              subscription_element=SubscriptionElement())


# ###### Misc

@bp.route('/subscription_elements/keep', methods=['POST'])
def batch_keep_html():
    params = process_request_values(request.values)
    data_params = get_params_value(params, 'subscription_element', True)
    if 'keep' not in data_params or data_params['keep'] not in ['yes', 'no', 'maybe', 'archive']:
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
    batch_update_subscription_element_keep(elements, data_params['keep'])
    return redirect(request.referrer)


@bp.route('/subscription_elements/<int:id>/keep', methods=['POST'])
def keep_html(id):
    element = get_or_abort(SubscriptionElement, id)
    value = request.args.get('keep')
    if value is None:
        flash("Keep argument not found.", 'error')
    else:
        flash("Element updated.")
        update_subscription_element_keep(element, value)
    return redirect(request.referrer)


@bp.route('/subscription_elements/<int:id>/keep.json', methods=['POST'])
def keep_json(id):
    element = get_or_error(SubscriptionElement, id)
    if isinstance(element, dict):
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
    update_subscription_element_keep(element, value)
    if has_preview:
        html = render_template_ws("subscription_elements/_element_preview.html", element=element)
    else:
        html = render_template_ws("subscription_elements/_element_display.html", element=element)
    return {'error': False, 'item': element.to_json(), 'html': strip_whitespace(html)}


@bp.route('/subscription_elements/<int:id>/redownload.json', methods=['POST'])
def redownload_json(id):
    element = get_or_error(SubscriptionElement, id)
    if isinstance(element, dict):
        return element
    if element.post is not None:
        return {'error': True, 'message': "Subscription element already has a post."}
    results = redownload_element(element)
    return _json_preview(results, element)


@bp.route('/subscription_elements/<int:id>/reinstantiate.json', methods=['POST'])
def reinstantiate_json(id):
    element = get_or_error(SubscriptionElement, id)
    if isinstance(element, dict):
        return element
    if element.status.name != 'archived':
        return {'error': True, 'message': 'Can only reinstantiate archived elements.'}
    results = reinstantiate_element(element)
    return _json_preview(results, element)


@bp.route('/subscription_elements/<int:id>/relink.json', methods=['POST'])
def relink_json(id):
    element = get_or_error(SubscriptionElement, id)
    if isinstance(element, dict):
        return element
    if element.status.name != 'unlinked':
        return {'error': True, 'message': "Can only relink unlinked elements."}
    results = relink_element(element)
    return _json_preview(results, element)


# #### Private functions

def _json_preview(results, element):
    if element.post is None:
        element.post_match = get_post_by_md5(element.md5)
        element.archive_match = get_archive('post', element.md5) if element.post_match is None else None
    results['item'] = element.to_json()
    results['html'] = render_template_ws("subscription_elements/_element_preview.html", element=element)
    return results
