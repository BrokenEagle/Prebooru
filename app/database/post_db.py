# APP/DATABASE/LOCAL.PY

# ##LOCAL IMPORTS
from .. import models, SESSION
from ..logical.utility import get_current_time
from .base_db import update_column_attributes


# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['width', 'height', 'file_ext', 'md5', 'size']
CREATE_ALLOWED_ATTRIBUTES = ['width', 'height', 'file_ext', 'md5', 'size']


# ##FUNCTIONS

# #### Route DB functions

# ###### Create

def create_post_from_parameters(createparams):
    current_time = get_current_time()
    post = models.Post(created=current_time)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(post, update_columns, createparams)
    print("[%s]: created" % post.shortlink)
    return post


# #### Misc functions

def create_post(width, height, file_ext, md5, size):
    return create_post_from_parameters({'width': width, 'height': height, 'file_ext': file_ext, 'md5': md5, 'size': size})


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
        posts += models.Post.query.filter(models.Post.id.in_(sublist)).all()
    return posts


def get_post_by_md5(md5):
    return models.Post.query.filter_by(md5=md5).first()
