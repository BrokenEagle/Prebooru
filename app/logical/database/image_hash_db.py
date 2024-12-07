# APP/LOGICAL/DATABASE/IMAGE_HASH_DB.PY

# ## LOCAL IMPORTS
from ...models import ImageHash
from .base_db import set_column_attributes, save_record, commit_or_flush


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = []
NULL_WRITABLE_ATTRIBUTES = ['post_id', 'ratio', 'hash']


# ## FUNCTIONS

# #### Create

def create_image_hash_from_parameters(post, createparams, commit=True):
    return set_image_hash_from_parameters(post, createparams, commit, 'create')


# #### Set

def set_image_hash_from_parameters(image_hash, setparams, commit, action):
    if set_column_attributes(image_hash, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(image_hash, commit, action)
    return image_hash


# ###### DELETE

def delete_image_hash_by_post_id(post_id):
    ImageHash.query.filter(ImageHash.post_id == post_id).delete()
    commit_or_flush(False)


# #### Misc functions

def get_image_hash_by_post_id(post_id):
    return ImageHash.query.filter(ImageHash.post_id == post_id).all()
