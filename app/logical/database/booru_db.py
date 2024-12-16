# APP/LOGICAL/DATABASE/BOORU_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ...models import Booru, Label
from .base_db import set_column_attributes, set_relationship_collections, set_association_attributes,\
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

ANY_WRITABLE_COLUMNS = ['danbooru_id', 'current_name', 'banned', 'deleted']
NULL_WRITABLE_ATTRIBUTES = []

UPDATE_ALLOWED_COLUMNS = set(COLUMN_ATTRIBUTES).intersection(UPDATE_ALLOWED_ATTRIBUTES)


# ## FUNCTIONS

# #### Create

def create_booru_from_parameters(createparams):
    booru = Booru()
    return set_booru_from_parameters(booru, createparams, 'created')


def create_booru_from_json(data):
    booru = Booru.loads(data)
    add_record(booru)
    commit_session()
    save_record(booru, 'created')
    return booru


# #### Update

def update_booru_from_parameters(booru, updateparams):
    return set_booru_from_parameters(booru, updateparams, 'updated')


def recreate_booru_relations(booru, updateparams):
    _set_relations(booru, updateparams)
    commit_session()


def will_update_booru(booru, data):
    return will_update_record(booru, data, UPDATE_ALLOWED_COLUMNS)


# #### Set

def set_booru_from_parameters(booru, setparams, action):
    _set_all_names(setparams, booru)
    col_result = set_column_attributes(booru, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams, safe=True)
    rel_result = _set_relations(booru, setparams)
    if col_result or rel_result:
        save_record(booru, action)
    return booru


# #### Delete

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

def _set_all_names(params, booru):
    if isinstance(params.get('current_name'), str):
        names = set(params.get('names', list(booru.names)) + [params['current_name']])
        params['names'] = list(names)


def _set_relations(booru, setparams, create=None):
    set_association_attributes(setparams, ASSOCIATION_ATTRIBUTES)
    return set_relationship_collections(booru, ALL_SCALAR_RELATIONSHIPS, setparams)
