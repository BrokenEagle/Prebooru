# APP/DATABASE/BOORU_DB.PY

# ##LOCAL IMPORTS
from .. import models, SESSION
from ..logical.utility import get_current_time
from ..sources.base_source import get_artist_id_source
from ..sources.danbooru_source import get_artist_by_id
from .base_db import update_column_attributes, update_relationship_collections


# ##GLOBAL VARIABLES


COLUMN_ATTRIBUTES = ['danbooru_id', 'current_name']
UPDATE_SCALAR_RELATIONSHIPS = [('names', 'name', models.Label)]
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
    booru = models.Booru(created=current_time, updated=current_time)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_column_attributes(booru, update_columns, createparams)
    create_relationships = [relationship for relationship in UPDATE_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    update_relationship_collections(booru, create_relationships, createparams)
    print("[%s]: created" % booru.shortlink)
    return booru


def create_booru_from_id(danbooru_id):
    data = get_artist_by_id(danbooru_id)
    if data['error']:
        return data
    createparams = {
        'danbooru_id': danbooru_id,
        'current_name': data['artist']['name'],
        'names': [data['artist']['name']],
    }
    booru = create_booru_from_parameters(createparams)
    return {'error': False, 'data': createparams, 'item': booru.to_json()}


# ###### Update


def update_booru_from_parameters(booru, updateparams):
    update_results = []
    set_all_names(updateparams, booru)
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(update_column_attributes(booru, update_columns, updateparams))
    update_relationships = [relationship for relationship in UPDATE_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    update_results.append(update_relationship_collections(booru, update_relationships, updateparams))
    if any(update_results):
        print("[%s]: updated" % booru.shortlink)
        booru.updated = get_current_time()
        SESSION.commit()


def query_update_booru(booru):
    booru_data = get_artist_by_id(booru.danbooru_id)
    if booru_data['error']:
        return booru_data
    updateparams = {
        'current_name': booru_data['artist']['name'],
    }
    update_booru_from_parameters(booru, updateparams)
    return {'error': False}


# ###### Misc routes

def check_artists_booru(booru):
    dirty = False
    data = get_artist_by_id(booru.danbooru_id, include_urls=True)
    if data['error']:
        return data
    existing_artist_ids = [artist.id for artist in booru.artists]
    artist_urls = [artist_url for artist_url in data['artist']['urls']]
    for artist_url in artist_urls:
        source = get_artist_id_source(artist_url['url'])
        if source is None:
            continue
        site_artist_id = int(source.get_artist_id_url_id(artist_url['url']))
        site_id = source.SITE_ID
        artist = models.Artist.query.filter_by(site_id=site_id, site_artist_id=site_artist_id).first()
        if artist is None or artist.id in existing_artist_ids:
            continue
        print("Adding artist #", artist.id)
        booru.artists.append(artist)
        SESSION.commit()
        dirty = True
    if dirty:
        booru.updated = get_current_time()
        SESSION.commit()
    return {'error': False}


# #### Misc functions

def booru_append_artist(booru, artist):
    booru.artists.append(artist)
    SESSION.commit()
