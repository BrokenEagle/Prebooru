# APP/LOGICAL/DATABASE/BOORU_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time
from utility.data import swap_key_value

# ## LOCAL IMPORTS
from ...models import Booru, Label
from .base_db import set_column_attributes, set_version_relations, will_update_record, add_record, save_record,\
    commit_session


# ## GLOBAL VARIABLES

VERSION_RELATIONSHIPS = [('name', 'names', 'name', Label)]

ANY_WRITABLE_COLUMNS = ['danbooru_id', 'banned', 'deleted']
NULL_WRITABLE_ATTRIBUTES = ['name_value']


# ## FUNCTIONS

# #### Create

def create_booru_from_parameters(createparams, commit=True):
    createparams.setdefault('banned', False)
    createparams.setdefault('deleted', False)
    swap_key_value(createparams, 'name', 'name_value')
    return set_booru_from_parameters(Booru(), createparams, 'created', commit, True)


def create_booru_from_json(data, commit=True):
    booru = Booru.loads(data)
    add_record(booru)
    commit_session()
    save_record(booru, 'created', commit=commit)
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
    col_result = set_column_attributes(booru, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES,
                                       setparams, update=update, safe=True)
    rel_result = _set_relations(booru, setparams, update)
    if col_result or rel_result:
        save_record(booru, action, commit=commit)
    return booru


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

def _set_relations(booru, params, update):
    return set_version_relations(booru, VERSION_RELATIONSHIPS, params, update=update)
