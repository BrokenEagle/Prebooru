# APP/LOGICAL/DATABASE/POST_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import or_

# ## PACKAGE IMPORTS
from utility.time import days_ago

# ## LOCAL IMPORTS
from ...models import Post, SubscriptionElement, ImageHash, IllustUrl, Illust, Artist
from .base_db import set_column_attributes, add_record, save_record, commit_session


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['type_name', 'simcheck', 'alternate', 'width', 'height', 'size', 'file_ext', 'md5',
                        'pixel_md5', 'duration', 'audio']
NULL_WRITABLE_ATTRIBUTES = ['danbooru_id']

SUBELEMENT_SUBCLAUSE = SubscriptionElement.query.filter(SubscriptionElement.post_id.is_not(None))\
                                                .with_entities(SubscriptionElement.post_id)
NO_SUBELEMENT_CLAUSE = Post.id.not_in(SUBELEMENT_SUBCLAUSE)

SUBELEMENT_SUBQUERY = SubscriptionElement.query.filter(SubscriptionElement.post_id.is_not(None))\
                                               .with_entities(SubscriptionElement.post_id)


# ## FUNCTIONS

# #### Create

def create_post_from_parameters(createparams, commit=True):
    post = Post(alternate=False, simcheck=False)
    return set_post_from_parameters(post, createparams, 'created', commit)


def create_post_from_json(data, commit=True):
    post = Post.loads(data)
    add_record(post)
    save_record(post, 'created', commit=commit)
    return post


# #### Update

def update_post_from_parameters(post, updateparams, commit=True):
    return set_post_from_parameters(post, updateparams, 'updated', commit)


# #### Set

def set_post_from_parameters(post, setparams, action, commit):
    if set_column_attributes(post, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(post, action, commit=commit)
    return post


# #### Misc

def create_post(width, height, file_ext, md5, size, post_type, pixel_md5, duration, has_audio):
    params = {
        'width': width,
        'height': height,
        'file_ext': file_ext,
        'md5': md5,
        'size': size,
        'type_name': post_type,
        'pixel_md5': pixel_md5,
        'duration': duration,
        'audio': has_audio,
    }
    return create_post_from_parameters(params)


def create_post_and_add_illust_url(illust_url, width, height, file_ext, md5, size, post_type, pixel_md5, duration,
                                   has_audio):
    post = create_post(width, height, file_ext, md5, size, post_type, pixel_md5, duration, has_audio)
    illust_url.post_id = post.id
    commit_session()
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
    return Post.query.filter(Post.simcheck.is_(False),
                             or_(Post.type_value == 'user', Post.id.not_in(SUBELEMENT_SUBQUERY)))


def get_all_posts_page(limit):
    return Post.query.count_paginate(per_page=limit)


def get_posts_to_query_danbooru_id_page(limit):
    query = Post.query.join(IllustUrl, Post.illust_urls).join(Illust, IllustUrl.illust).join(Artist, Illust.artist)
    query = query.filter(Post.danbooru_id.is_(None), Artist.primary.is_(True), NO_SUBELEMENT_CLAUSE)
    return query.limit_paginate(per_page=limit)


def get_artist_posts_without_danbooru_ids(artist):
    query = artist._post_query.filter(Post.danbooru_id.is_(None))
    return query.limit_paginate(per_page=100, distinct=True)
