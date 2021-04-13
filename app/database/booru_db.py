# APP/DATABASE/BOORU_DB.PY

# ##LOCAL IMPORTS
from .. import models, SESSION
from ..logical.utility import GetCurrentTime
from ..sources.base_source import GetArtistIdSource
from ..sources.danbooru_source import GetArtistByID
from .base_db import UpdateColumnAttributes, UpdateRelationshipCollections


# ##GLOBAL VARIABLES


COLUMN_ATTRIBUTES = ['danbooru_id', 'current_name']
UPDATE_SCALAR_RELATIONSHIPS = [('names', 'name', models.Label)]
APPEND_SCALAR_RELATIONSHIPS = []

CREATE_ALLOWED_ATTRIBUTES = ['danbooru_id', 'current_name', 'names']
UPDATE_ALLOWED_ATTRIBUTES = ['current_name', 'names']


# ## FUNCTIONS

# #### Helper functions


def SetAllNames(params, booru):
    if 'current_name' in params:
        if booru is not None:
            params['names'] = params['names'] if 'names' in params else [booru_name.name for booru_name in booru.names]
        else:
            params['names'] = params['names'] if 'names' in params else []
        params['names'] = list(set(params['names'] + [params['current_name']]))


# #### Router helper functions

# ###### Create


def CreateBooruFromParameters(createparams):
    current_time = GetCurrentTime()
    SetAllNames(createparams, None)
    booru = models.Booru(created=current_time, updated=current_time)
    settable_keylist = set(createparams.keys()).intersection(CREATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    UpdateColumnAttributes(booru, update_columns, createparams)
    create_relationships = [relationship for relationship in UPDATE_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    UpdateRelationshipCollections(booru, create_relationships, createparams)
    return booru


def CreateBooruFromID(danbooru_id):
    data = GetArtistByID(danbooru_id)
    if data['error']:
        return data
    createparams = {
        'danbooru_id': danbooru_id,
        'current_name': data['artist']['name'],
        'names': [data['artist']['name']],
    }
    booru = CreateBooruFromParameters(createparams)
    return {'error': False, 'data': createparams, 'item': booru.to_json()}


# ###### Update


def UpdateBooruFromParameters(booru, updateparams):
    update_results = []
    SetAllNames(updateparams, booru)
    settable_keylist = set(updateparams.keys()).intersection(UPDATE_ALLOWED_ATTRIBUTES)
    update_columns = settable_keylist.intersection(COLUMN_ATTRIBUTES)
    update_results.append(UpdateColumnAttributes(booru, update_columns, updateparams))
    update_relationships = [relationship for relationship in UPDATE_SCALAR_RELATIONSHIPS if relationship[0] in settable_keylist]
    update_results.append(UpdateRelationshipCollections(booru, update_relationships, updateparams))
    if any(update_results):
        print("Changes detected.")
        booru.updated = GetCurrentTime()
        SESSION.commit()


def QueryUpdateBooru(booru):
    booru_data = GetArtistByID(booru.danbooru_id)
    if booru_data['error']:
        return booru_data
    updateparams = {
        'current_name': booru_data['artist']['name'],
    }
    UpdateBooruFromParameters(booru, updateparams)
    return {'error': False}


# ###### Misc routes

def CheckArtistsBooru(booru):
    dirty = False
    data = GetArtistByID(booru.danbooru_id, include_urls=True)
    if data['error']:
        return data
    existing_artist_ids = [artist.id for artist in booru.artists]
    artist_urls = [artist_url for artist_url in data['artist']['urls']]
    for artist_url in artist_urls:
        source = GetArtistIdSource(artist_url['url'])
        if source is None:
            continue
        site_artist_id = int(source.GetArtistIdUrlId(artist_url['url']))
        site_id = source.SITE_ID
        artist = models.Artist.query.filter_by(site_id=site_id, site_artist_id=site_artist_id).first()
        if artist is None or artist.id in existing_artist_ids:
            continue
        print("Adding artist #", artist.id)
        booru.artists.append(artist)
        SESSION.commit()
        dirty = True
    if dirty:
        booru.updated = GetCurrentTime()
        SESSION.commit()
    return {'error': False}


# #### Misc functions

def BooruAppendArtist(booru, artist):
    booru.artists.append(artist)
    SESSION.commit()
