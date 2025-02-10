# APP/LOGICAL/DATABASE/ARCHIVE_ILLUST_DB.PY

# ## LOCAL IMPORTS
from ...models import ArchiveIllust
from .base_db import set_column_attributes, save_record, set_timesvalue


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['site_id', 'site_illust_id', 'site_artist_id', 'site_created', 'title', 'commentary', 'pages',
                        'score', 'active', 'created', 'updated', 'urls_json', 'titles_json', 'commentaries_json',
                        'additional_commentaries_json', 'tags_json', 'notations_json']
NULL_WRITABLE_ATTRIBUTES = ['archive_id']


# ## FUNCTIONS

# #### Create

def create_archive_illust_from_parameters(createparams, commit=True):
    return set_archive_illust_from_parameters(ArchiveIllust(), createparams, 'created', commit)


# #### Update

def update_archive_illust_from_parameters(archive_illust, updateparams, commit=True):
    return set_archive_illust_from_parameters(archive_illust, updateparams, 'updated', commit)


# #### Set

def set_archive_illust_from_parameters(archive_illust, setparams, action, commit):
    set_timesvalue(setparams, 'site_created')
    set_timesvalue(setparams, 'created')
    set_timesvalue(setparams, 'updated')
    if set_column_attributes(archive_illust, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(archive_illust, action, commit=commit)
    return archive_illust
