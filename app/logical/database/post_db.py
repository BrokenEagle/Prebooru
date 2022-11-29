# APP/LOGICAL/DATABASE/POST_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time, days_ago

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Post, SubscriptionElement
from .base_db import update_column_attributes
from .pool_element_db import delete_pool_element


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['width', 'height', 'file_ext', 'md5', 'size', 'danbooru_id', 'created', 'type_id', 'alternate',
                     'pixel_md5', 'duration', 'audio']
CREATE_ALLOWED_ATTRIBUTES = ['width', 'height', 'file_ext', 'md5', 'size', 'type_id', 'pixel_md5', 'duration', 'audio']
UPDATE_ALLOWED_ATTRIBUTES = ['width', 'height', 'duration', 'audio', 'danbooru_id']

SUBELEMENT_SUBCLAUSE = SubscriptionElement.query.filter(SubscriptionElement.post_id.is_not(None))\
                                                .with_entities(SubscriptionElement.post_id)
NO_SUBELEMENT_CLAUSE = Post.id.not_in(SUBELEMENT_SUBCLAUSE)


# ## FUNCTIONS

# #### Route DB functions

# ###### Create

def create_post_from_parameters(createparams):
    current_time = get_current_time()
    post = Post(created=current_time, alternate=False)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(post, update_columns, createparams)
    print("[%s]: created" % post.shortlink)
    return post


def create_post_from_json(data):
    post = Post.loads(data)
    SESSION.add(post)
    SESSION.commit()
    print("[%s]: created" % post.shortlink)
    return post


# ###### Update

def update_post_from_parameters(post, updateparams):
    update_results = []
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(update_column_attributes(post, update_columns, updateparams))
    if any(update_results):
        print("[%s]: updated" % post.shortlink)
        SESSION.commit()


def set_post_alternate(post, alternate):
    post.alternate = alternate
    SESSION.commit()


def set_post_type(post, post_type):
    post.type_id = Post.type_enum.by_name(post_type).id
    SESSION.commit()


# ###### Delete

def delete_post(post):
    for pool_element in post._pools:
        delete_pool_element(pool_element)
    SESSION.delete(post)
    SESSION.commit()


# #### Misc functions

def create_post(width, height, file_ext, md5, size, post_type, pixel_md5, duration, has_audio):
    params = {
        'width': width,
        'height': height,
        'file_ext': file_ext,
        'md5': md5,
        'size': size,
        'type_id': Post.type_enum.by_name(post_type).id,
        'pixel_md5': pixel_md5,
        'duration': duration,
        'audio': has_audio,
    }
    return create_post_from_parameters(params)


def post_append_illust_url(post, illust_url):
    post.illust_urls.append(illust_url)
    SESSION.commit()


def create_post_and_add_illust_url(illust_url, width, height, file_ext, md5, size, post_type, pixel_md5, duration,
                                   has_audio):
    post = create_post(width, height, file_ext, md5, size, post_type, pixel_md5, duration, has_audio)
    post_append_illust_url(post, illust_url)
    return post


def copy_post(post):
    """Return an uncommitted copy of the post."""
    return Post(**post.column_dict())


# #### Query functions

def get_posts_by_id(ids):
    posts = []
    for i in range(0, len(ids), 100):
        sublist = ids[i: i + 100]
        posts += Post.query.filter(Post.id.in_(sublist)).all()
    return posts


def get_posts_by_md5s(md5s):
    posts = []
    for i in range(0, len(md5s), 100):
        sublist = md5s[i: i + 100]
        posts += Post.query.filter(Post.md5.in_(sublist)).all()
    return posts


def get_post_by_md5(md5):
    return Post.query.filter_by(md5=md5).one_or_none()


def alternate_posts_query(days):
    return Post.query.filter(Post.created < days_ago(days), Post.alternate.is_(False))


def get_all_posts_page(limit):
    return Post.query.count_paginate(per_page=limit)


def get_posts_to_query_danbooru_id_page(limit):
    query = Post.query.filter(Post.danbooru_id.is_(None), NO_SUBELEMENT_CLAUSE)
    return query.limit_paginate(per_page=limit)
