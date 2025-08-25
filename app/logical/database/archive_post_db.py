# APP/LOGICAL/DATABASE/ARCHIVE_POST_DB.PY

# ## LOCAL IMPORTS
from ...models import ArchivePost
from .base_db import set_column_attributes, save_record, set_timesvalue


# ## GLOBAL VARIABLES

ANY_WRITABLE_ATTRIBUTES = ['md5', 'width', 'height', 'file_ext', 'size', 'danbooru_id', 'created', 'type_id', 'frames',
                           'pixel_md5', 'duration', 'audio', 'tags_json', 'notations_json', 'errors_json']
NULL_WRITABLE_ATTRIBUTES = ['archive_id']


# ## FUNCTIONS

# #### Create

def create_archive_post_from_parameters(createparams, commit=True):
    return set_archive_post_from_parameters(ArchivePost(), createparams, 'created', commit)


# #### Update

def update_archive_post_from_parameters(archive_post, updateparams, commit=True):
    return set_archive_post_from_parameters(archive_post, updateparams, 'updated', commit)


# #### Set

def set_archive_post_from_parameters(archive_post, setparams, action, commit):
    set_timesvalue(setparams, 'created')
    if set_column_attributes(archive_post, ANY_WRITABLE_ATTRIBUTES, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(archive_post, action, commit=commit)
    return archive_post
