# APP/LOGICAL/DATABASE/ARCHIVE_ARTIST_DB.PY

# ## LOCAL IMPORTS
from ...models import ArchiveArtist
from .base_db import set_column_attributes, save_record, set_timesvalue


# ## GLOBAL VARIABLES

ANY_WRITABLE_ATTRIBUTES = ['site_id', 'site_artist_id', 'site_created', 'site_account', 'name', 'profile', 'active',
                           'primary', 'created', 'updated', 'webpages_json', 'site_accounts_json', 'names_json',
                           'profiles_json', 'notations_json', 'boorus_json']
NULL_WRITABLE_ATTRIBUTES = ['archive_id']


# ## FUNCTIONS

# #### Create

def create_archive_artist_from_parameters(createparams, commit=True):
    return set_archive_artist_from_parameters(ArchiveArtist(), createparams, 'created', commit)


# #### Update

def update_archive_artist_from_parameters(archive_artist, updateparams, commit=True):
    return set_archive_artist_from_parameters(archive_artist, updateparams, 'updated', commit)


# #### Set

def set_archive_artist_from_parameters(archive_artist, setparams, action, commit):
    set_timesvalue(setparams, 'site_created')
    set_timesvalue(setparams, 'created')
    set_timesvalue(setparams, 'updated')
    if set_column_attributes(archive_artist, ANY_WRITABLE_ATTRIBUTES, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(archive_artist, action, commit=commit)
    return archive_artist
