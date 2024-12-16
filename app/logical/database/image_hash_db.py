# APP/LOGICAL/DATABASE/IMAGE_HASH_DB.PY

# ## LOCAL IMPORTS
from ...models import ImageHash
from .base_db import set_column_attributes, save_record, flush_session


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = []
NULL_WRITABLE_ATTRIBUTES = ['post_id', 'ratio', 'hash']


# ## FUNCTIONS

# #### Create

def create_image_hash_from_parameters(createparams):
    image_hash = ImageHash()
    return set_image_hash_from_parameters(image_hash, createparams, 'created')


# #### Set

def set_image_hash_from_parameters(image_hash, setparams, action):
    if set_column_attributes(image_hash, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(image_hash, action)
    return image_hash


# #### Delete

def delete_image_hash_by_post_id(post_id):
    ImageHash.query.filter(ImageHash.post_id == post_id).delete()
    flush_session()


# #### Query

def get_image_hash_by_post_id(post_id):
    return ImageHash.query.filter(ImageHash.post_id == post_id).all()
