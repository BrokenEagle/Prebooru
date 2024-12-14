# APP/LOGICAL/DATABASE/POST_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import or_

# ## PACKAGE IMPORTS
from utility.time import get_current_time, days_ago

# ## LOCAL IMPORTS
from ...models import Post, SubscriptionElement, ImageHash
from .base_db import update_column_attributes, add_record, delete_record, save_record, commit_session, flush_session
from .pool_element_db import delete_pool_element


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['width', 'height', 'file_ext', 'md5', 'size', 'danbooru_id', 'created', 'type_id', 'alternate',
                     'pixel_md5', 'duration', 'audio']
CREATE_ALLOWED_ATTRIBUTES = ['width', 'height', 'file_ext', 'md5', 'size', 'type_id', 'pixel_md5', 'duration', 'audio']
UPDATE_ALLOWED_ATTRIBUTES = ['width', 'height', 'file_ext', 'md5', 'size', 'type_id', 'pixel_md5', 'duration', 'audio',
                             'danbooru_id']

SUBELEMENT_SUBCLAUSE = SubscriptionElement.query.filter(SubscriptionElement.post_id.is_not(None))\
                                                .with_entities(SubscriptionElement.post_id)
NO_SUBELEMENT_CLAUSE = Post.id.not_in(SUBELEMENT_SUBCLAUSE)

TYPE_CLAUSE = Post.type_filter('name', '__eq__', 'user')
SUBELEMENT_SUBQUERY = SubscriptionElement.query.filter(SubscriptionElement.post_id.is_not(None))\
                                               .with_entities(SubscriptionElement.post_id)


# ## FUNCTIONS

# #### Route DB functions

# ###### Create

def create_post_from_parameters(createparams):
    current_time = get_current_time()
    post = Post(created=current_time, alternate=False, simcheck=False)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(post, update_columns, createparams)
    save_record(post, 'created')
    return post


def create_post_from_json(data):
    post = Post.loads(data)
    add_record(post)
    save_record(post, 'created')
    return post


# ###### Update

def update_post_from_parameters(post, updateparams):
    update_results = []
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(update_column_attributes(post, update_columns, updateparams))
    if any(update_results):
        save_record(post, 'updated')


def set_post_alternate(post, alternate):
    post.alternate = alternate
    commit_session()


def set_post_type(post, post_type):
    post.type_id = Post.type_enum.by_name(post_type).id
    commit_session()


def set_post_simcheck(post, simcheck):
    post.simcheck = simcheck
    flush_session()


# ###### Delete

def delete_post(post):
    for pool_element in post._pools:
        delete_pool_element(pool_element)
    delete_record(post)
    commit_session()


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
    illust_url.post_id = post.id
    commit_session()


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


def missing_image_hashes_query():
    return Post.query.filter(Post.id.not_in(ImageHash.query.with_entities(ImageHash.post_id)))


def missing_similarity_matches_query():
    query = Post.query.enum_join(Post.type_enum)
    return query.filter(Post.simcheck.is_(False), or_(TYPE_CLAUSE, Post.id.not_in(SUBELEMENT_SUBQUERY)))


def get_all_posts_page(limit):
    return Post.query.count_paginate(per_page=limit)


def get_posts_to_query_danbooru_id_page(limit):
    query = Post.query.filter(Post.danbooru_id.is_(None), NO_SUBELEMENT_CLAUSE)
    return query.limit_paginate(per_page=limit)


def get_artist_posts_without_danbooru_ids(artist):
    query = artist._post_query.filter(Post.danbooru_id.is_(None))
    return query.limit_paginate(per_page=100, distinct=True)
