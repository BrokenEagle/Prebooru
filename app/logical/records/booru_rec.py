# APP/LOGICAL/RECORDS/BOORU_REC.PY

# ## LOCAL IMPORTS
from ..sources.base import get_artist_id_source
from ..sources.danbooru import get_artist_by_id
from ..database.artist_db import get_site_artist
from ..database.booru_db import create_booru_from_parameters, update_booru_from_parameters, booru_append_artist


# ## FUNCTIONS

def create_booru_from_source(danbooru_id):
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


def update_booru_from_source(booru):
    booru_data = get_artist_by_id(booru.danbooru_id)
    if booru_data['error']:
        return booru_data
    updateparams = {
        'current_name': booru_data['artist']['name'],
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
