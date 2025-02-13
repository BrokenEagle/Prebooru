# APP/CONTROLLERS/POSTS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template, redirect, url_for, flash
from werkzeug.datastructures import ImmutableMultiDict, CombinedMultiDict
from sqlalchemy import not_, or_
from sqlalchemy.orm import lazyload, selectinload

# ## PACKAGE IMPORTS
from utility.data import eval_bool_string, is_falsey

# ## LOCAL IMPORTS
from ..models import Post, Illust, IllustUrl, Artist, PoolElement, PostType
from ..logical.records.post_rec import create_sample_preview_files, create_video_sample_preview_files,\
    archive_post_for_deletion, redownload_post, delete_post, save_post_to_archive
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_or_abort, index_html_response


# ## GLOBAL VARIABLES

bp = Blueprint("post", __name__)

POST_POOLS_SUBQUERY = Post.query.join(PoolElement, Post.pool_elements)\
                                .filter(Post.id == PoolElement.post_id,
                                        PoolElement.type_value == 'pool_post')\
                                .with_entities(Post.id)
ILLUST_POOLS_SUBQUERY = Post.query.join(IllustUrl, Post.illust_urls)\
                                  .join(Illust, IllustUrl.illust)\
                                  .join(PoolElement, Illust.pool_elements)\
                                  .filter(Illust.id == PoolElement.illust_id,
                                          PoolElement.type_value == 'pool_ilust')\
                                  .with_entities(Post.id)

POOL_SEARCH_KEYS = ['has_any_pool', 'has_post_pool', 'has_illust_pool']

DEFAULT_DELETE_EXPIRES = 30  # Days

# #### Load options

SHOW_HTML_OPTIONS = (
    selectinload(Post.illust_urls).selectinload(IllustUrl.illust).options(
        selectinload(Illust.tags),
        selectinload(Illust.title),
        selectinload(Illust.commentary),
        selectinload(Illust.artist).selectinload(Artist.boorus),
        # Eager load all posts underneath the same illust(s)
        selectinload(Illust.urls).selectinload(IllustUrl.post).lazyload('*'),
    ),
    selectinload(Post.notations),
    selectinload(Post.errors),
    selectinload(Post.pool_elements).selectinload(PoolElement.pool),
)

INDEX_HTML_OPTIONS = (
    lazyload('*'),
)

JSON_OPTIONS = (
    selectinload(Post.illust_urls),
    selectinload(Post.errors),
)

MAX_LIMIT_HTML = 100


# ## FUNCTIONS

# #### Query functions

def pool_filter(query, search):
    pool_search_key = next((key for key in POOL_SEARCH_KEYS if key in search), None)
    if pool_search_key is not None and eval_bool_string(search[pool_search_key]) is not None:
        if pool_search_key == 'has_any_pool':
            subclause = or_(Post.id.in_(POST_POOLS_SUBQUERY), Post.id.in_(ILLUST_POOLS_SUBQUERY))
        elif pool_search_key == 'has_post_pool':
            subclause = Post.id.in_(POST_POOLS_SUBQUERY)
        elif pool_search_key == 'has_illust_pool':
            subclause = Post.id.in_(ILLUST_POOLS_SUBQUERY)
        if is_falsey(search[pool_search_key]):
            subclause = not_(subclause)
        query = query.filter(subclause)
    elif 'pool_id' in search or 'pool_id_not' in search:
        if search.get('pool_id', "").isdigit():
            subquery = PoolElement.query.filter(PoolElement.pool_id == int(search['pool_id']),
                                                PoolElement.type_value == 'pool_post')\
                                        .with_entities(PoolElement.post_id)
            query = query.filter(Post.id.in_(subquery))
        if search.get('pool_id_not', "").isdigit():
            subquery = PoolElement.query.filter(PoolElement.pool_id == int(search['pool_id_not']),
                                                PoolElement.type_value == 'pool_post')\
                                        .with_entities(PoolElement.post_id)
            query = query.filter(Post.id.not_in(subquery))
    return query


# #### Route auxiliary functions

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    negative_search = get_params_value(params, 'not', True)
    q = Post.query
    q = search_filter(q, search, negative_search)
    q = pool_filter(q, search)
    if search.get('order') == 'site':
        q = q.unique_join(IllustUrl, Post.illust_urls)\
             .unique_join(Illust, IllustUrl.illust)\
             .order_by(Illust.site_created.desc())
    else:
        q = default_order(q, search)
    return q


# #### Route functions

# ###### SHOW

@bp.route('/posts/<int:id>.json', methods=['GET'])
def show_json(id):
    return show_json_response(Post, id, JSON_OPTIONS)


@bp.route('/posts/<int:id>', methods=['GET'])
def show_html(id):
    post = get_or_abort(Post, id, options=SHOW_HTML_OPTIONS)
    return render_template("posts/show.html", post=post)


# ###### INDEX

@bp.route('/posts.json', methods=['GET'])
def index_json():
    q = index()
    q = q.options(JSON_OPTIONS)
    return index_json_response(q, request, distinct=True)


@bp.route('/posts', methods=['GET'])
def index_html():
    q = index()
    if request.args.get('search[type]') is None:
        post_type = request.args.get('type')
        if PostType.has_name(post_type):
            q = q.filter(Post.type_value == post_type)
    q = q.options(INDEX_HTML_OPTIONS)
    page = paginate(q, request, max_limit=MAX_LIMIT_HTML, distinct=True)
    edit_posts = request.values.get('edit_posts', type=eval_bool_string, default=False)
    return index_html_response(page, 'post', 'posts', edit_posts=edit_posts)


@bp.route('/', methods=['GET'])
def bare_index_html():
    # Shave of any input parameters; only the `/posts` endpoint will be allowed to process those.
    request.args = ImmutableMultiDict([])
    request.values = CombinedMultiDict([request.args])
    return index_html()


# ###### DELETE

@bp.route('/posts/<int:id>/archive', methods=['DELETE'])
def soft_delete_html(id):
    post = get_or_abort(Post, id)
    expires = request.values.get('expires', DEFAULT_DELETE_EXPIRES, type=int)
    results = archive_post_for_deletion(post, expires)
    if results['error']:
        flash(results['message'], 'error')
        if not results['is_deleted']:
            return redirect(request.referrer)
    if results['is_deleted']:
        flash("Post deleted.")
    return redirect(url_for('archive.show_html', id=results['item']['id']))


@bp.route('/posts/<int:id>', methods=['DELETE'])
def hard_delete_html(id):
    post = get_or_abort(Post, id)
    results = delete_post(post)
    if results['error']:
        flash(results['message'], 'error')
        if not results['is_deleted']:
            return redirect(request.referrer)
    if results['is_deleted']:
        flash("Post deleted.")
    return redirect(url_for('post.index_html'))


# ###### MISC

@bp.route('/posts/<int:id>/archive', methods=['POST'])
def archive_post_html(id):
    post = get_or_abort(Post, id)
    results = save_post_to_archive(post, None)
    if results['error']:
        flash(results['message'], 'error')
        return redirect(request.referrer)
    flash("Post archived.")
    return redirect(url_for('archive.show_html', id=results['item']['id']))


@bp.route('/posts/<int:id>/regenerate_previews', methods=['POST'])
def regenerate_previews_html(id):
    post = get_or_abort(Post, id)
    results = create_sample_preview_files(post)
    if post.is_video:
        create_video_sample_preview_files(post)
    if results['error']:
        flash(results['message'], 'error')
    else:
        flash("Previews regenerated.")
    return redirect(url_for('post.show_html', id=post.id))


@bp.route('/posts/<int:id>/redownload', methods=['POST'])
def redownload_html(id):
    post = get_or_abort(Post, id)
    if not redownload_post(post):
        flash("Unable to redownload post.", 'error')
    else:
        flash("Post redownloaded.")
    return redirect(url_for('post.show_html', id=post.id))
