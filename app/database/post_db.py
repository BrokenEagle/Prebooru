# APP/DATABASE/LOCAL.PY

# ##LOCAL IMPORTS
from .. import models, SESSION
from ..logical.utility import GetCurrentTime
from .base_db import UpdateColumnAttributes


# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['width', 'height', 'file_ext', 'md5', 'size']
CREATE_ALLOWED_ATTRIBUTES = ['width', 'height', 'file_ext', 'md5', 'size']


# ##FUNCTIONS

# #### Route DB functions

# ###### Create

def CreatePostFromParameters(createparams):
    current_time = GetCurrentTime()
    post = models.Post(created=current_time)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    UpdateColumnAttributes(post, update_columns, createparams)
    return post


# #### Misc functions

def CreatePost(width, height, file_ext, md5, size):
    return CreatePostFromParameters({'width': width, 'height': height, 'file_ext': file_ext, 'md5': md5, 'size': size})


def PostAppendIllustUrl(post, illust_url):
    post.illust_urls.append(illust_url)
    SESSION.commit()


def CreatePostAndAddIllustUrl(illust_url, width, height, file_ext, md5, size):
    post = CreatePost(width, height, file_ext, md5, size)
    PostAppendIllustUrl(post, illust_url)
    return post


# #### Query functions

def GetPostsByID(ids):
    posts = []
    for i in range(0, len(ids), 100):
        sublist = ids[i: i + 100]
        posts += models.Post.query.filter(models.Post.id.in_(sublist)).all()
    return posts


def GetPostByMD5(md5):
    return models.Post.query.filter_by(md5=md5).first()
