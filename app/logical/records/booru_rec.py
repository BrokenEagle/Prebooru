# APP/LOGICAL/RECORDS/BOORU_REC.PY

# ## PACKAGE IMPORTS
from utility.print import error_print

# ## LOCAL IMPORTS
from ... import SESSION
from ..utility import set_error
from ..sources.base import get_artist_id_source
from ..sources.danbooru import get_artist_by_id
from ..database.artist_db import get_site_artist
from ..database.booru_db import create_booru_from_parameters, update_booru_from_parameters, booru_append_artist,\
    get_booru, create_booru_from_raw_parameters, delete_booru
from ..database.archive_data_db import get_archive_data, create_archive_data, update_archive_data


# ## FUNCTIONS

def create_booru_from_source(danbooru_id):
    data = get_artist_by_id(danbooru_id)
    if data['error']:
        return data
    createparams = {
        'danbooru_id': danbooru_id,
        'current_name': data['artist']['name'],
        'names': [data['artist']['name']],
        'banned': data['artist']['is_banned'],
        'deleted': data['artist']['is_deleted'],
    }
    booru = create_booru_from_parameters(createparams)
    return {'error': False, 'data': createparams, 'item': booru.to_json()}


def update_booru_from_source(booru):
    booru_data = get_artist_by_id(booru.danbooru_id)
    if booru_data['error']:
        return booru_data
    updateparams = {
        'current_name': booru_data['artist']['name'],
        'deleted': booru_data['artist']['is_deleted'],
        'banned': booru_data['artist']['is_banned'],
    }
    update_booru_from_parameters(booru, updateparams)
    return {'error': False}


def update_booru_artists_from_source(booru):
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
        artist = get_site_artist(site_artist_id, site_id)
        if artist is None or artist.id in existing_artist_ids:
            continue
        booru_append_artist(booru, artist)
    return {'error': False}


def archive_booru_for_deletion(booru):
    retdata = {'error': False}
    retdata = _archive_booru_data(booru, retdata)
    if retdata['error']:
        return retdata
    return _delete_booru_data(booru, retdata)


def recreate_archived_booru(data):
    retdata = {'error': False}
    booru_data = data['body']
    booru = get_booru(booru_data['danbooru_id'])
    if booru is not None:
        return set_error(retdata, "Booru already exists: booru #%d" % booru.id)
    if len(data['scalars']['names']):
        booru_data['names'] = data['scalars']['names']
    try:
        booru = create_booru_from_raw_parameters(data['body'])
    except Exception as e:
        error_print(e)
        return set_error(retdata, "Error creating booru: %s" % repr(e))
    retdata['item'] = booru.to_json()
    return retdata


# #### Private functions

def _archive_booru_data(booru, retdata):
    data = {
        'body': booru.archive_dict(),
        'scalars': {
            'names': list(booru.names),
        },
        'relations': {},
        'links': {},
    }
    data_key = '%d' % (booru.danbooru_id)
    archive_data = get_archive_data('booru', data_key)
    try:
        if archive_data is None:
            create_archive_data('booru', data_key, data, 30)
        else:
            update_archive_data(archive_data, data, 30)
    except Exception as e:
        return set_error(retdata, "Error archiving data: %s" % str(e))
    return retdata


def _delete_booru_data(booru, retdata):
    try:
        delete_booru(booru)
    except Exception as e:
        SESSION.rollback()
        return set_error(retdata, "Error deleting booru: %s" % str(e))
    return retdata
