# APP/LOGICAL/DATABASE/ARCHIVE_BOORU_DB.PY

# ## LOCAL IMPORTS
from ...models import ArchiveBooru
from .base_db import set_column_attributes, save_record, set_timesvalue


# ## GLOBAL VARIABLES

ANY_WRITABLE_ATTRIBUTES = ['danbooru_id', 'name', 'banned', 'deleted', 'created', 'updated', 'names_json',
                           'notations_json', 'artists_json']
NULL_WRITABLE_ATTRIBUTES = ['archive_id']


# ## FUNCTIONS

# #### Create

def create_archive_booru_from_parameters(createparams, commit=True):
    return set_archive_booru_from_parameters(ArchiveBooru(), createparams, 'created', commit)


# #### Update

def update_archive_booru_from_parameters(archive_booru, updateparams, commit=True):
    return set_archive_booru_from_parameters(archive_booru, updateparams, 'updated', commit)


# #### Set

def set_archive_booru_from_parameters(archive_booru, setparams, action, commit):
    set_timesvalue(setparams, 'site_created')
    set_timesvalue(setparams, 'created')
    set_timesvalue(setparams, 'updated')
    if set_column_attributes(archive_booru, ANY_WRITABLE_ATTRIBUTES, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(archive_booru, action, commit=commit)
    return archive_booru
