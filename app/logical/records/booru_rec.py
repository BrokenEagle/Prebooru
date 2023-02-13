# APP/LOGICAL/RECORDS/BOORU_REC.PY

# ## LOCAL IMPORTS
from ... import SESSION
from ...enum_imports import site_descriptor
from ..utility import set_error
from ..sources.base_src import get_artist_id_source
from ..sources.danbooru_src import get_artist_by_id, get_artists_by_ids
from ..database.artist_db import get_site_artist
from ..database.booru_db import create_booru_from_parameters, update_booru_from_parameters, booru_append_artist,\
    get_booru, create_booru_from_json, delete_booru, get_all_boorus_page, recreate_booru_relations
from ..database.notation_db import create_notation_from_json
from .base_rec import delete_data
from .archive_rec import archive_record


# ## FUNCTIONS

def check_all_boorus():
    print("Checking all boorus for updated data.")
    status = {'total': 0}
    page = get_all_boorus_page(100)
    while True:
        print(f"check_all_boorus: {page.first} - {page.last} / Total({page.count})")
        if len(page.items) == 0 or not check_boorus(page.items, status) or not page.has_next:
            return status
        page = page.next()


def check_boorus(boorus, status):
    danbooru_ids = [booru.danbooru_id for booru in boorus]
    results = get_artists_by_ids(danbooru_ids)
    if results['error']:
        print(results['message'])
        return False
    for data in results['artists']:
        booru = next(filter(lambda x: x.danbooru_id == data['id'], boorus))
        updates = {'current_name': data['name'], 'deleted': data['is_deleted'], 'banned': data['is_banned']}
        if update_booru_from_parameters(booru, updates):
            status['total'] += 1
    return True


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
        artist = get_site_artist(site_artist_id, source.SITE.id)
        if artist is None or artist.id in existing_artist_ids:
            continue
        booru_append_artist(booru, artist)
    return {'error': False}


def archive_booru_for_deletion(booru):
    retdata = {'error': False}
    retdata, _archive = archive_record(booru, 30, retdata)
    if retdata['error']:
        return retdata
    return delete_data(booru, delete_booru, retdata)


def recreate_archived_booru(data):
    retdata = {'error': False}
    booru = get_booru(data['body']['danbooru_id'])
    if booru is not None:
        return set_error(retdata, "Booru already exists: booru #%d" % booru.id)
    booru = create_booru_from_json(data['body'])
    if len(data['scalars']['names']):
        recreate_booru_relations(booru, {'names': data['scalars']['names']})
    retdata['item'] = booru.to_json()
    relink_archived_booru(data, booru)
    for notation_data in data['relations']['notations']:
        notation = create_notation_from_json(notation_data)
        booru.notations.append(notation)
        SESSION.commit()
    return retdata


def recreate_archived_booru2(data):
    retdata, booru = recreate_record(data, get_booru, create_booru_from_json,
                                     ['site_artist_id', 'site'], {'error': False})
    if retdata['error']:
        return retdata
    recreate_relations(data, booru, recreate_booru_relations, {})
    relink_relations(data, booru, {'boorus': })
    
    if len(data['scalars']['names']):
        recreate_booru_relations(booru, {'names': data['scalars']['names']})
    retdata['item'] = booru.to_json()
    relink_archived_booru(data, booru)
    for notation_data in data['relations']['notations']:
        notation = create_notation_from_json(notation_data)
        booru.notations.append(notation)
        SESSION.commit()
    return retdata


def relink_archived_booru(data, booru=None):
    if booru is None:
        booru = get_booru(data['body']['danbooru_id'])
        if booru is None:
            return "No booru found with Danbooru ID %d" % data['body']['danbooru_id']
    for artist_key in data['links']['artists']:
        site_name, site_artist_id = artist_key.split('-')
        site_id = site_descriptor[site_name].value
        site_artist_id = int(site_artist_id)
        artist = get_site_artist(site_artist_id, site_id)
        if artist is None:
            continue
        booru_append_artist(booru, artist)
