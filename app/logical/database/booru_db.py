# APP/LOGICAL/DATABASE/BOORU_DB.PY

# ##LOCAL IMPORTS
from ... import SESSION
from ...models import Booru, Label
from ..utility import get_current_time
from .base_db import update_column_attributes, update_relationship_collections, set_association_attributes


# ##GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['danbooru_id', 'current_name']
UPDATE_SCALAR_RELATIONSHIPS = [('_names', 'name', Label)]
APPEND_SCALAR_RELATIONSHIPS = []
ASSOCIATION_ATTRIBUTES = ['names']

CREATE_ALLOWED_ATTRIBUTES = ['danbooru_id', 'current_name', '_names']
UPDATE_ALLOWED_ATTRIBUTES = ['current_name', '_names']


# ## FUNCTIONS

# #### Helper functions

def set_all_names(params, booru):
    if 'current_name' in params and params['current_name']:
        booru_names = list(booru.names) if booru is not None else []
        params['names'] = params['names'] if 'names' in params else booru_names
        params['names'] = list(set(params['names'] + [params['current_name']]))


# #### Router helper functions

# ###### Create

def create_booru_from_parameters(createparams):
    current_time = get_current_time()
    set_all_names(createparams, None)
    set_association_attributes(createparams, ASSOCIATION_ATTRIBUTES)
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
    set_association_attributes(updateparams, ASSOCIATION_ATTRIBUTES)
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
    print("[%s]: Adding %s" % (booru.shortlink, artist.shortlink))
    booru.artists.append(artist)
    booru.updated = get_current_time()
    SESSION.commit()
