# APP/LOGICAL/DATABASE/BOORU_DB.PY

# ##LOCAL IMPORTS
from ... import SESSION
from ...models import Booru, Label
from ..utility import get_current_time
from .base_db import update_column_attributes, update_relationship_collections


# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['danbooru_id', 'current_name']
UPDATE_SCALAR_RELATIONSHIPS = [('names', 'name', Label)]
APPEND_SCALAR_RELATIONSHIPS = []

CREATE_ALLOWED_ATTRIBUTES = ['danbooru_id', 'current_name', 'names']
UPDATE_ALLOWED_ATTRIBUTES = ['current_name', 'names']


# ## FUNCTIONS

# #### Helper functions


def set_all_names(params, booru):
    if 'current_name' in params:
        if booru is not None:
            params['names'] = params['names'] if 'names' in params else [booru_name.name for booru_name in booru.names]
        else:
            params['names'] = params['names'] if 'names' in params else []
        params['names'] = list(set(params['names'] + [params['current_name']]))


# #### Router helper functions

# ###### Create


def create_booru_from_parameters(createparams):
    current_time = get_current_time()
    set_all_names(createparams, None)
    booru = Booru(created=current_time, updated=current_time)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(booru, update_columns, createparams)
    create_relationships = [rel for rel in UPDATE_SCALAR_RELATIONSHIPS if rel[0] in settable_keylist]
    update_relationship_collections(booru, create_relationships, createparams)
    print("[%s]: created" % booru.shortlink)
    return booru


# ###### Update


def update_booru_from_parameters(booru, updateparams):
    update_results = []
    set_all_names(updateparams, booru)
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(update_column_attributes(booru, update_columns, updateparams))
    update_relationships = [rel for rel in UPDATE_SCALAR_RELATIONSHIPS if rel[0] in settable_keylist]
    update_results.append(update_relationship_collections(booru, update_relationships, updateparams))
    if any(update_results):
        print("[%s]: updated" % booru.shortlink)
        booru.updated = get_current_time()
        SESSION.commit()


# #### Misc functions

def booru_append_artist(booru, artist):
    print("[%s]: Adding %s", (booru.shortlink, artist.shortlink))
    booru.artists.append(artist)
    booru.updated = get_current_time()
    SESSION.commit()
