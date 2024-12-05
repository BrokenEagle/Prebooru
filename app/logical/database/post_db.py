# APP/LOGICAL/DATABASE/POST_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import or_

# ## PACKAGE IMPORTS
from utility.time import days_ago

# ## LOCAL IMPORTS
from ...models import Post, SubscriptionElement, ImageHash, MediaAsset
from .base_db import set_column_attributes, commit_or_flush, add_record, delete_record, save_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['type_id', 'simcheck']
NULL_WRITABLE_ATTRIBUTES = ['media_asset_id', 'danbooru_id']

SUBELEMENT_SUBCLAUSE = SubscriptionElement.query.filter(SubscriptionElement.post_id.is_not(None))\
                                                .with_entities(SubscriptionElement.post_id)
NO_SUBELEMENT_CLAUSE = Post.id.not_in(SUBELEMENT_SUBCLAUSE)

TYPE_CLAUSE = Post.type_filter('name', '__eq__', 'user')
SUBELEMENT_SUBQUERY = SubscriptionElement.query.filter(SubscriptionElement.post_id.is_not(None))\
                                               .with_entities(SubscriptionElement.post_id)


# ## FUNCTIONS

# #### Create

def create_post_from_parameters(createparams, commit=True):
    if 'type' in createparams:
        createparams['type_id'] = Post.type_enum.by_name(createparams['type']).id
    createparams['simcheck'] = False
    return set_post_from_parameters(Post(), createparams, commit, 'created')


def create_post_from_json(data):
    post = Post.loads(data)
    add_record(post)
    commit_or_flush(True, safe=True)
    print("[%s]: created" % post.shortlink)
    return post


# ###### Update

def update_post_from_parameters(post, updateparams, commit=True):
    return set_post_from_parameters(post, updateparams, commit, 'updated')


# #### Set

def set_post_from_parameters(post, setparams, commit, action):
    if 'type' in setparams:
        setparams['type_id'] = Post.type_enum.by_name(setparams['type']).id
    if set_column_attributes(post, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(post, commit, action)
    return post


# ###### Delete

def delete_post(post):
    for pool_element in post._pools:
        delete_pool_element(pool_element)
    delete_record(post)
    commit_or_flush(True)


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
        'location_id': MediaAsset.location_enum.primary.id,
    }
    return create_post_from_parameters(params)


def post_append_illust_url(post, illust_url):
    illust_url.post_id = post.id
    commit_or_flush(False)


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
        posts += Post.query.join(MediaAsset).filter(MediaAsset.md5.in_(sublist)).all()
    return posts


def get_post_by_md5(md5):
    return Post.query.filter_by(md5=md5).one_or_none()


def alternate_posts_query(days):
    return Post.query.join(MediaAsset).enum_join(MediaAsset.location_enum)\
                     .filter(Post.created < days_ago(days),
                             MediaAsset.location_filter('name', '__eq__', 'alternate'))


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
