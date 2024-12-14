# APP/LOGICAL/DATABASE/IMAGE_HASH_DB.PY

# ## LOCAL IMPORTS
from ...models import ImageHash
from .base_db import update_column_attributes, save_record, flush_session


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = []
NULL_WRITABLE_ATTRIBUTES = ['post_id', 'ratio', 'hash']


# ## FUNCTIONS

# #### DB functions

# ###### CREATE

def create_image_hash_from_parameters(createparams, commit=False):
    image_hash = ImageHash()
    update_column_attributes(image_hash, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, createparams)
    save_record(image_hash, 'created', commit=commit)
    return image_hash


# ###### DELETE

def delete_image_hash_by_post_id(post_id):
    ImageHash.query.filter(ImageHash.post_id == post_id).delete()
    flush_session()


# #### Misc functions

def get_image_hash_by_post_id(post_id):
    return ImageHash.query.filter(ImageHash.post_id == post_id).all()
