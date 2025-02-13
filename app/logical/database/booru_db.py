# APP/LOGICAL/DATABASE/BOORU_DB.PY

# ## PACKAGE IMPORTS
from utility.time import get_current_time
from utility.data import swap_key_value

# ## LOCAL IMPORTS
from ...models import Booru
from .base_db import set_column_attributes, set_version_relations, will_update_record, save_record,\
    commit_session, set_timesvalue


# ## GLOBAL VARIABLES

VERSION_RELATIONSHIPS = [('name_value', 'name_values')]

ANY_WRITABLE_COLUMNS = ['danbooru_id', 'banned', 'deleted']
NULL_WRITABLE_ATTRIBUTES = ['name_value', 'created', 'updated']


# ## FUNCTIONS

# #### Create

def create_booru_from_parameters(createparams, commit=True):
    createparams.setdefault('banned', False)
    createparams.setdefault('deleted', False)
    set_timesvalue(createparams, 'created')
    set_timesvalue(createparams, 'updated')
    return set_booru_from_parameters(Booru(), createparams, 'created', commit, True)


# #### Update

def update_booru_from_parameters(booru, updateparams, commit=True, update=True):
    return set_booru_from_parameters(booru, updateparams, 'updated', commit, update)


def will_update_booru(booru, data):
    return will_update_record(booru, data, ANY_WRITABLE_COLUMNS)


# #### Set

def set_booru_from_parameters(booru, setparams, action, commit, update):
    swap_key_value(setparams, 'name', 'name_value')
    col_result = set_column_attributes(booru, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES,
                                       setparams, update=update, safe=True)
    ver_result = set_version_relations(booru, VERSION_RELATIONSHIPS, setparams, update=update)\
        if action == 'updated' else False
    if col_result or ver_result:
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
