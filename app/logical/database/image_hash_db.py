# APP/LOGICAL/DATABASE/IMAGE_HASH_DB.PY

# ## LOCAL IMPORTS
from ...models import ImageHash
from .base_db import set_column_attributes, save_record, flush_session


# ## GLOBAL VARIABLES

ANY_WRITABLE_ATTRIBUTES = []
NULL_WRITABLE_ATTRIBUTES = ['post_id', 'ratio', 'hash']


# ## FUNCTIONS

# #### Create

def create_image_hash_from_parameters(createparams, commit=True):
    image_hash = ImageHash()
    return set_image_hash_from_parameters(image_hash, createparams, 'created', commit)


# #### Set

def set_image_hash_from_parameters(image_hash, setparams, action, commit):
    if set_column_attributes(image_hash, ANY_WRITABLE_ATTRIBUTES, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(image_hash, action, commit=commit)
    return image_hash


# #### Delete

def delete_image_hash_by_post_id(post_id):
    ImageHash.query.filter(ImageHash.post_id == post_id).delete()
    flush_session()
