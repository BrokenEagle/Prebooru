# APP/LOGICAL/DATABASE/BOORU_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ...models import Booru, Label
from .base_db import set_column_attributes, set_relationship_collections, set_association_attributes,\
    will_update_record, add_record, delete_record, save_record, commit_session


# ## GLOBAL VARIABLES

UPDATE_SCALAR_RELATIONSHIPS = [('_names', 'name', Label)]
APPEND_SCALAR_RELATIONSHIPS = []
ASSOCIATION_ATTRIBUTES = ['names']

ANY_WRITABLE_COLUMNS = ['danbooru_id', 'current_name', 'banned', 'deleted']
NULL_WRITABLE_ATTRIBUTES = []


# ## FUNCTIONS

# #### Create

def create_booru_from_parameters(createparams, commit=True):
    booru = Booru()
    return set_booru_from_parameters(booru, createparams, 'created', commit, True)


def create_booru_from_json(data):
    booru = Booru.loads(data)
    add_record(booru)
    commit_session()
    save_record(booru, 'created')
    return booru


# #### Update

def update_booru_from_parameters(booru, updateparams, commit=True, update=True):
    return set_booru_from_parameters(booru, updateparams, 'updated', commit, update)


def recreate_booru_relations(booru, updateparams):
    if _set_relations(booru, updateparams, False):
        commit_session()


def will_update_booru(booru, data):
    return will_update_record(booru, data, ANY_WRITABLE_COLUMNS)


# #### Set

def set_booru_from_parameters(booru, setparams, action, commit, update):
    _set_all_names(setparams, booru)
    col_result = set_column_attributes(booru, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES,
                                       setparams, update=update, safe=True)
    rel_result = _set_relations(booru, setparams, update)
    if col_result or rel_result:
        save_record(booru, action, commit=commit)
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


def _set_relations(booru, setparams, update):
    set_association_attributes(setparams, ASSOCIATION_ATTRIBUTES)
    return set_relationship_collections(booru, UPDATE_SCALAR_RELATIONSHIPS, setparams, update=update)
