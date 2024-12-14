# APP/LOGICAL/DATABASE/BOORU_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ...models import Booru, Label
from .base_db import update_column_attributes, update_relationship_collections, set_association_attributes,\
    will_update_record, add_record, delete_record, save_record, commit_session


# ## GLOBAL VARIABLES

COLUMN_ATTRIBUTES = ['danbooru_id', 'current_name', 'banned', 'deleted']
UPDATE_SCALAR_RELATIONSHIPS = [('_names', 'name', Label)]
APPEND_SCALAR_RELATIONSHIPS = []
ALL_SCALAR_RELATIONSHIPS = UPDATE_SCALAR_RELATIONSHIPS + APPEND_SCALAR_RELATIONSHIPS
ASSOCIATION_ATTRIBUTES = ['names']
NORMALIZED_ASSOCIATE_ATTRIBUTES = ['_' + key for key in ASSOCIATION_ATTRIBUTES]

CREATE_ALLOWED_ATTRIBUTES = ['danbooru_id', 'current_name', 'banned', 'deleted', '_names']
UPDATE_ALLOWED_ATTRIBUTES = ['danbooru_id', 'current_name', 'banned', 'deleted', '_names']

UPDATE_ALLOWED_COLUMNS = set(COLUMN_ATTRIBUTES).intersection(UPDATE_ALLOWED_ATTRIBUTES)


# ## FUNCTIONS

# #### Helper functions

def set_all_names(params, booru):
    if 'current_name' in params and params['current_name']:
        booru_names = list(booru.names) if booru is not None else []
        params['names'] = params.get('names', booru_names)
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
    _update_relations(booru, createparams, create=True)
    save_record(booru, 'created')
    return booru


def create_booru_from_json(data):
    booru = Booru.loads(data)
    add_record(booru)
    commit_session()
    save_record(booru, 'created')
    return booru


# ###### Update

def update_booru_from_parameters(booru, updateparams):
    update_results = []
    set_all_names(updateparams, booru)
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(update_column_attributes(booru, update_columns, updateparams))
    update_results.append(_update_relations(booru, updateparams, create=False))
    if any(update_results):
        booru.updated = get_current_time()
        save_record(booru, 'updated')
        return True
    return False


def recreate_booru_relations(booru, updateparams):
    _update_relations(booru, updateparams, create=False)


def will_update_booru(booru, data):
    return will_update_record(booru, data, UPDATE_ALLOWED_COLUMNS)


# ###### Delete

def delete_booru(booru):
    delete_record(booru)
    commit_session()


# #### Misc functions

def booru_append_artist(booru, artist):
    print("[%s]: Adding %s" % (booru.shortlink, artist.shortlink))
    booru.artists.append(artist)
    booru.updated = get_current_time()
    commit_session()


def booru_remove_artist(booru, artist):
    print("[%s]: Removing %s" % (booru.shortlink, artist.shortlink))
    booru.artists.remove(artist)
    booru.updated = get_current_time()
    commit_session()


# #### Query functions

def get_booru(danbooru_id):
    return Booru.query.filter_by(danbooru_id=danbooru_id).one_or_none()


def get_boorus(danbooru_ids):
    return Booru.query.filter(Booru.danbooru_id.in_(danbooru_ids)).all()


def get_all_boorus_page(limit):
    return Booru.query.count_paginate(per_page=limit)


# #### Private functions

def _update_relations(booru, updateparams, create=None):
    set_association_attributes(updateparams, ASSOCIATION_ATTRIBUTES)
    allowed_attributes = CREATE_ALLOWED_ATTRIBUTES if create else UPDATE_ALLOWED_ATTRIBUTES
    settable_keylist = set(updateparams.keys()).intersection(allowed_attributes)
    update_relationships = [rel for rel in UPDATE_SCALAR_RELATIONSHIPS if rel[0] in settable_keylist]
    return update_relationship_collections(booru, update_relationships, updateparams)
