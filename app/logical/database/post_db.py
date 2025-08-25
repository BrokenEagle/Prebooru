# APP/LOGICAL/DATABASE/POST_DB.PY

# ## EXTERNAL IMPORTS
from sqlalchemy import or_

# ## PACKAGE IMPORTS
from utility.time import days_ago

# ## LOCAL IMPORTS
from ...models import Post, SubscriptionElement, ImageHash, IllustUrl, Illust, Artist
from .base_db import set_column_attributes, save_record, set_timesvalue


# ## GLOBAL VARIABLES

ANY_WRITABLE_ATTRIBUTES = ['type_name', 'simcheck', 'alternate', 'width', 'height', 'size', 'file_ext', 'md5',
                           'pixel_md5', 'duration', 'audio', 'frames', 'ugoira_id']
NULL_WRITABLE_ATTRIBUTES = ['danbooru_id', 'created']

SUBELEMENT_SUBQUERY = Post.query.join(IllustUrl, Post.illust_urls)\
                                .join(SubscriptionElement, IllustUrl.subscription_element)\
                                .filter(SubscriptionElement.status_value == 'active')\
                                .with_entities(Post.id)


# ## FUNCTIONS

# #### Create

def create_post_from_parameters(createparams, commit=True):
    createparams.setdefault('alternate', False)
    createparams.setdefault('simcheck', False)
    set_timesvalue(createparams, 'created')
    return set_post_from_parameters(Post(), createparams, 'created', commit)


# #### Update

def update_post_from_parameters(post, updateparams, commit=True):
    return set_post_from_parameters(post, updateparams, 'updated', commit)


# #### Set

def set_post_from_parameters(post, setparams, action, commit):
    if set_column_attributes(post, ANY_WRITABLE_ATTRIBUTES, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(post, action, commit=commit)
    return post


# #### Query functions

def get_posts_by_id(ids):
    posts = []
    for i in range(0, len(ids), 100):
        sublist = ids[i: i + 100]
        posts += Post.query.filter(Post.id.in_(sublist)).all()
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


def get_posts_to_query_danbooru_id_query(limit):
    query = Post.query.join(IllustUrl, Post.illust_urls).join(Illust, IllustUrl.illust).join(Artist, Illust.artist)
    return query.filter(Post.danbooru_id.is_(None), Artist.primary.is_(True), Post.id.not_in(SUBELEMENT_SUBQUERY))


def get_artist_posts_without_danbooru_ids_query(artist):
    return artist._post_query.filter(Post.danbooru_id.is_(None))


def get_posts_by_subscription_elements(elements):
    query = Post.query.join(IllustUrl, Post.illust_urls).join(SubscriptionElement, IllustUrl.subscription_element)
    return query.filter(SubscriptionElement.id.in_(element.id for element in elements)).all()
