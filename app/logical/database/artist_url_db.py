# APP/LOGICAL/DATABASE/ARTIST_URL_DB.PY

# ## LOCAL IMPORTS
from ...models import ArtistUrl
from .base_db import set_column_attributes, add_record, save_record


# ## GLOBAL VARIABLES

ANY_WRITABLE_COLUMNS = ['active']
NULL_WRITABLE_ATTRIBUTES = ['artist_id', 'url']


# ## FUNCTIONS

# #### Create

def create_artist_url_from_parameters(createparams, commit=True):
    artist_url = ArtistUrl()
    return set_artist_url_from_parameters(artist_url, createparams, 'created', commit)


def create_artist_url_from_json(data, commit=True):
    artist_url = ArtistUrl.loads(data)
    add_record(artist_url)
    save_record(artist_url, 'created', commit=commit)
    return artist_url


# #### Update

def update_artist_url_from_parameters(artist_url, updateparams, commit=True):
    return set_artist_url_from_parameters(artist_url, updateparams, 'updated', commit)


# #### Set

def set_artist_url_from_parameters(artist_url, setparams, action, commit):
    if set_column_attributes(artist_url, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(artist_url, action, commit=commit)
    return artist_url
