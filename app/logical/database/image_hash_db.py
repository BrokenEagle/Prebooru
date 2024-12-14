# APP/LOGICAL/DATABASE/IMAGE_HASH_DB.PY

# ## LOCAL IMPORTS
from ...models import ImageHash
from .base_db import update_column_attributes, flush_session, commit_or_flush


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['post_id', 'ratio', 'hash']

CREATE_ALLOWED_ATTRIBUTES = ['post_id', 'ratio', 'hash']


# ## FUNCTIONS

# #### DB functions

# ###### CREATE

def create_image_hash_from_parameters(createparams, commit=False):
    image_hash = ImageHash()
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(image_hash, update_columns, createparams, commit=False)
    print("[%s]: created" % image_hash.shortlink)
    commit_or_flush(commit)
    return image_hash


# ###### DELETE

def delete_image_hash_by_post_id(post_id):
    ImageHash.query.filter(ImageHash.post_id == post_id).delete()
    flush_session()


# #### Misc functions

def get_image_hash_by_post_id(post_id):
    return ImageHash.query.filter(ImageHash.post_id == post_id).all()
