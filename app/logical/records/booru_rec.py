# APP/LOGICAL/RECORDS/BOORU_REC.PY

# ## PACKAGE IMPORTS
from utility.data import merge_dicts
from utility.uprint import print_info

# ## LOCAL IMPORTS
from ...models import ArchiveBooru, BooruNames, Label
from ..utility import set_error
from ..logger import handle_error_message
from ..sources.base_src import get_artist_id_source
from ..sources.danbooru_src import get_artist_by_id, get_artists_by_ids
from ..database.base_db import delete_record, commit_session
from ..database.artist_db import get_site_artist, get_site_artists
from ..database.booru_db import create_booru_from_parameters, update_booru_from_parameters, booru_append_artist,\
    get_all_boorus_page, will_update_booru, get_booru
from ..database.notation_db import create_notation_from_parameters
from ..database.archive_db import create_archive_from_parameters, update_archive_from_parameters,\
    get_archive_by_booru_name
from ..database.archive_booru_db import create_archive_booru_from_parameters, update_archive_booru_from_parameters
from .base_rec import delete_data, delete_version_relation, swap_version_relation


# ## FUNCTIONS

def check_all_boorus():
    print("Checking all boorus for updated data.")
    status = {'total': 0}
    page = get_all_boorus_page(100)
    while True:
        print_info(f"\ncheck_all_boorus: {page.first} - {page.last} / Total({page.count})\n")
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
        updates = {'name': data['name'], 'deleted': data['is_deleted'], 'banned': data['is_banned']}
        if will_update_booru(booru, updates):
            update_booru_from_parameters(booru, updates)
            status['total'] += 1
    return True


def create_booru_from_source(danbooru_id):
    data = get_artist_by_id(danbooru_id)
    if data['error']:
        return data
    createparams = {
        'danbooru_id': danbooru_id,
        'name': data['artist']['name'],
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
        'name': booru_data['artist']['name'],
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


def delete_booru(booru, retdata=None):
    """Hard delete. Continue as long as booru record gets deleted."""

    def _delete(booru):
        msg = "[%s]: deleted\n" % booru.shortlink
        delete_record(booru)
        commit_session()
        print(msg)

    retdata = retdata or {'error': False, 'is_deleted': False}
    retdata.update(delete_data(booru, _delete))
    if retdata['error']:
        return retdata
    retdata['is_deleted'] = True
    return retdata


def archive_booru_for_deletion(booru, days_to_expire):
    """Soft delete. Preserve data at all costs."""
    retdata = {'error': False, 'is_deleted': False}
    retdata.update(save_booru_to_archive(booru, days_to_expire))
    if retdata['error']:
        return retdata
    return delete_booru(booru, retdata)


def save_booru_to_archive(booru, days_to_expire):
    retdata = {'error': False}
    archive = get_archive_by_booru_name(booru.name_value)
    if archive is None:
        archive = create_archive_from_parameters({'days': days_to_expire, 'type_name': 'booru'}, commit=False)
    else:
        update_archive_from_parameters(archive, {'days': days_to_expire}, commit=False)
    retdata['item'] = archive.basic_json()
    archive_params = {k: v for (k, v) in booru.basic_json().items() if k in ArchiveBooru.basic_attributes}
    archive_params['name'] = booru.name_value
    archive_params['names_json'] = list(booru.name_values)
    archive_params['notations_json'] = [{'body': notation.body,
                                         'created': notation.created.isoformat(),
                                         'updated': notation.updated.isoformat()}
                                        for notation in booru.notations]
    archive_params['artists_json'] = [{'site': artist.site_name,
                                       'site_artist_id': artist.site_artist_id}
                                      for artist in booru.artists]
    if archive.booru_data is None:
        archive_params['archive_id'] = archive.id
        create_archive_booru_from_parameters(archive_params)
    else:
        update_archive_booru_from_parameters(archive.booru_data, archive_params)
    return retdata


def recreate_archived_booru(archive):
    booru_data = archive.booru_data
    booru = get_booru(booru_data.danbooru_id)
    if booru is not None:
        return handle_error_message(f"Booru already exists: {booru.shortlink}")
    booru = create_booru_from_parameters(booru_data.recreate_json(), commit=False)
    booru.name_values.extend(booru_data.names_json)
    _link_artists(booru, booru_data)
    for notation in booru_data.notations_json:
        createparams = merge_dicts(notation, {'booru_id': booru.id})
        create_notation_from_parameters(createparams, commit=False)
    retdata = {'error': False, 'item': booru.basic_json()}
    commit_session()
    update_archive_from_parameters(archive, {'days': 7})
    return retdata


def relink_archived_booru(archive):
    booru_data = archive.booru_data
    booru = get_booru(booru_data.danbooru_id)
    if booru is None:
        msg = f"danbooru #{booru_data.danbooru_id} not found in boorus."
        return handle_error_message(msg)
    retdata = {'error': False, 'item': booru.basic_json()}
    _link_artists(booru, booru_data)
    commit_session()
    return retdata


def booru_delete_name(booru, label_id):
    return delete_version_relation(booru, Label, BooruNames, label_id, 'booru_id', 'label_id', 'Names')


def booru_swap_name(booru, label_id):
    return swap_version_relation(booru, Label, BooruNames, label_id, 'booru_id', 'label_id', 'name', 'names', 'Names')


# ## Private functions

def _relation_params_check(booru, model, m2m_model, model_id, model_field, name):
    retdata = {'error': False}
    attach = model.find(model_id)
    if attach is None:
        return set_error(retdata, "%s #%d does not exist." % (model.model_name, model_id))
    retdata['attach'] = attach
    m2m_row = m2m_model.query.filter_by(**{'booru_id': booru.id, model_field: model_id}).one_or_none()
    if m2m_row is None:
        msg = "%s with %s does not exist on %s." % (name, attach.shortlink, booru.shortlink)
        return set_error(retdata, msg)
    return retdata


def _link_artists(booru, booru_data):
    if booru_data.artists is None:
        return
    artists = get_site_artists(list(booru_data.artists))
    booru.artists.extend(artists)
