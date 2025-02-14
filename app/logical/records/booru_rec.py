# APP/LOGICAL/RECORDS/BOORU_REC.PY

# ## PACKAGE IMPORTS
from utility.uprint import print_info

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Booru, BooruNames, Label
from ..utility import set_error
from ..logger import handle_error_message
from ..sources.base_src import get_artist_id_source
from ..sources.danbooru_src import get_artist_by_id, get_artists_by_ids
from ..database.base_db import delete_record, commit_session
from ..database.artist_db import get_site_artist
from ..database.booru_db import create_booru_from_parameters, update_booru_from_parameters, booru_append_artist,\
    get_all_boorus_page, will_update_booru
from ..database.archive_db import set_archive_temporary
from .base_rec import delete_data
from .archive_rec import archive_record, recreate_record, recreate_scalars, recreate_attachments, recreate_links


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


def archive_booru_for_deletion(booru, expires=30):
    archive = archive_record(booru, expires)
    if archive is None:
        return handle_error_message(f"Error archiving data [{booru.shortlink}].")
    retdata = {'item': archive.to_json()}
    retdata.update(delete_data(booru, delete_booru))
    return retdata


def recreate_archived_booru(archive):
    try:
        booru = recreate_record(Booru, archive.key, archive.data)
        recreate_scalars(booru, archive.data)
        recreate_attachments(booru, archive.data)
        recreate_links(booru, archive.data)
    except Exception as e:
        retdata = handle_error_message(e)
        SESSION.rollback()
    else:
        retdata = {'error': False, 'item': booru.to_json()}
        set_archive_temporary(archive, 7)
        SESSION.commit()
    return retdata


def relink_archived_booru(archive):
    booru = Booru.find_by_key(archive.key)
    if booru is None:
        return f"No booru found with key {archive.key}"
    recreate_links(booru, archive.data)


def delete_booru(booru):
    msg = "[%s]: deleted\n" % booru.shortlink
    delete_record(booru)
    commit_session()
    print(msg)


def booru_delete_name(booru, label_id):
    retdata = _relation_params_check(booru, Label, BooruNames, label_id, 'label_id', 'Site account')
    if retdata['error']:
        return retdata
    BooruNames.query.filter_by(booru_id=booru.id, label_id=label_id).delete()
    commit_session()
    return retdata


def booru_swap_name(booru, label_id):
    retdata = _relation_params_check(booru, Label, BooruNames, label_id, 'label_id', 'Name')
    if retdata['error']:
        return retdata
    BooruNames.query.filter_by(booru_id=booru.id, label_id=label_id).delete()
    swap = booru.name
    booru.name = retdata['attach']
    if swap is not None:
        booru.names.append(swap)
    commit_session()
    return retdata


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
