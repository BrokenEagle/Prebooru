# APP/CONTROLLERS/POSTS_CONTROLLER.PY

# ## EXTERNAL IMPORTS
from flask import Blueprint, request, render_template
from sqlalchemy import not_, or_
from sqlalchemy.orm import lazyload, selectinload

# ## LOCAL IMPORTS
from ..models import Post, Illust, IllustUrl, Artist, PoolPost, PoolIllust
from ..logical.utility import eval_bool_string, is_falsey
from .base_controller import show_json_response, index_json_response, search_filter, process_request_values,\
    get_params_value, paginate, default_order, get_or_abort


# ## GLOBAL VARIABLES

bp = Blueprint("post", __name__)

POST_POOLS_SUBQUERY = Post.query.join(PoolPost, Post._pools).filter(Post.id == PoolPost.post_id).with_entities(Post.id)
ILLUST_POOLS_SUBQUERY = Post.query.join(IllustUrl, Post.illust_urls).join(Illust, IllustUrl.illust)\
                            .join(PoolIllust, Illust._pools).filter(Illust.id == PoolIllust.illust_id)\
                            .with_entities(Post.id)

POOL_SEARCH_KEYS = ['has_pools', 'has_post_pools', 'has_illust_pools']


# #### Load options

SHOW_HTML_OPTIONS = (
    selectinload(Post.illust_urls).selectinload(IllustUrl.illust).options(
        selectinload(Illust._tags),
        selectinload(Illust._commentaries),
        selectinload(Illust.artist).selectinload(Artist.boorus),
        # Eager load all posts underneath the same illust(s)
        selectinload(Illust.urls).selectinload(IllustUrl.post).lazyload('*'),
    ),
    selectinload(Post.notations),
    selectinload(Post.errors),
    selectinload(Post._pools).selectinload(PoolPost.pool),
)

INDEX_HTML_OPTIONS = (
    lazyload('*'),
)

JSON_OPTIONS = (
    selectinload(Post.illust_urls),
    selectinload(Post.errors),
)


# ## FUNCTIONS

# #### Query functions

def pool_filter(query, search):
    pool_search_key = next((key for key in POOL_SEARCH_KEYS if key in search), None)
    if pool_search_key is not None and eval_bool_string(search[pool_search_key]) is not None:
        if pool_search_key == 'has_pools':
            subclause = or_(Post.id.in_(POST_POOLS_SUBQUERY), Post.id.in_(ILLUST_POOLS_SUBQUERY))
        elif pool_search_key == 'has_post_pools':
            subclause = Post.id.in_(POST_POOLS_SUBQUERY)
        elif pool_search_key == 'has_illust_pools':
            subclause = Post.id.in_(ILLUST_POOLS_SUBQUERY)
        if is_falsey(search[pool_search_key]):
            subclause = not_(subclause)
        query = query.filter(subclause)
    elif 'pool_id' in search and search['pool_id'].isdigit():
        query = query.unique_join(PoolPost, Post._pools).filter(PoolPost.pool_id == int(search['pool_id']))
    return query


# #### Route auxiliary functions

def index():
    params = process_request_values(request.values)
    search = get_params_value(params, 'search', True)
    negative_search = get_params_value(params, 'not', True)
    q = Post.query
    q = search_filter(q, search, negative_search)
    q = pool_filter(q, search)
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
    return index_json_response(q, request)


@bp.route('/', methods=['GET'])
@bp.route('/posts', methods=['GET'])
def index_html():
    q = index()
    q = q.options(INDEX_HTML_OPTIONS)
    posts = paginate(q, request)
    return render_template("posts/index.html", posts=posts, post=Post())
