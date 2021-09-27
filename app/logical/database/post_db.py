# APP/LOGICAL/DATABASE/POST_DB.PY

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Post
from ..utility import get_current_time
from .base_db import update_column_attributes


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['width', 'height', 'file_ext', 'md5', 'size', 'danbooru_id']
CREATE_ALLOWED_ATTRIBUTES = ['width', 'height', 'file_ext', 'md5', 'size']
UPDATE_ALLOWED_ATTRIBUTES = ['danbooru_id']


# ## FUNCTIONS

# #### Route DB functions

# ###### Create

def create_post_from_parameters(createparams):
    current_time = get_current_time()
    post = Post(created=current_time)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(post, update_columns, createparams)
    print("[%s]: created" % post.shortlink)
    return post


# ###### Upadate

def update_post_from_parameters(post, updateparams):
    update_results = []
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(update_column_attributes(post, update_columns, updateparams))
    if any(update_results):
        print("[%s]: updated" % post.shortlink)
        SESSION.commit()


# #### Misc functions

def create_post(width, height, file_ext, md5, size):
    params = {'width': width, 'height': height, 'file_ext': file_ext, 'md5': md5, 'size': size}
    return create_post_from_parameters(params)


def post_append_illust_url(post, illust_url):
    post.illust_urls.append(illust_url)
    SESSION.commit()


def create_post_and_add_illust_url(illust_url, width, height, file_ext, md5, size):
    post = create_post(width, height, file_ext, md5, size)
    post_append_illust_url(post, illust_url)
    return post


# #### Query functions

def get_posts_by_id(ids):
    posts = []
    for i in range(0, len(ids), 100):
        sublist = ids[i: i + 100]
        posts += Post.query.filter(Post.id.in_(sublist)).all()
    return posts


def get_post_by_md5(md5):
    return Post.query.filter_by(md5=md5).first()