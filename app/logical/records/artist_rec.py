# APP/LOGICAL/RECORDS/ARTIST_REC.PY

# ## PYTHON IMPORTS
import itertools

# ## PACKAGE IMPORTS
from utility.data import inc_dict_entry, merge_dicts, swap_key_value
from utility.uprint import print_info

# ## LOCAL IMPORTS
from ...models import ArchiveArtist, ArtistSiteAccounts, ArtistNames, ArtistProfiles, Description, Label
from ..utility import set_error
from ..logger import handle_error_message
from ..database.base_db import add_record, delete_record, commit_session
from ..database.artist_db import create_artist_from_parameters, update_artist_from_parameters_standard,\
    get_site_artist, get_artists_without_boorus_page, create_artist_from_json
from ..database.artist_url_db import create_artist_url_from_json
from ..database.booru_db import get_boorus, create_booru_from_parameters, booru_append_artist
from ..database.notation_db import create_notation_from_json
from ..database.archive_db import create_archive_from_parameters, update_archive_from_parameters,\
    get_archive_artist_by_site
from .base_rec import delete_data


# ## FUNCTIONS

def check_all_artists_for_boorus():
    print("Checking all artists for Danbooru artists.")
    status = {'total': 0, 'created': 0}
    page = get_artists_without_boorus_page(100)
    booru_dict = {}
    while True:
        print_info(f"\ncheck_all_artists_for_boorus: {page.first} - {page.last} / Total({page.count})\n")
        if len(page.items) == 0\
           or not check_artists_for_boorus(page.items, booru_dict, status)\
           or not page.has_next:
            return status
        page = page.next()


def check_artists_for_boorus(artists, booru_dict=None, status=None):
    from ..sources.danbooru_src import get_artists_by_multiple_urls
    booru_dict = booru_dict if booru_dict is not None else {}
    status = status if status is not None else {}
    query_urls = [artist.booru_search_url for artist in artists]
    query_urls = [url for url in query_urls if url is not None]
    results = get_artists_by_multiple_urls(query_urls)
    if results['error']:
        print(results['message'])
        return False
    if len(results['data']) > 0:
        danb_artists = itertools.chain(*[results['data'][url] for url in results['data']])
        danb_artist_ids = set(artist['id'] for artist in danb_artists if artist['id'] not in booru_dict)
        boorus = get_boorus(danb_artist_ids)
        booru_dict.update({booru.danbooru_id: booru for booru in boorus})
        for url in results['data']:
            add_danbooru_artists(url, results['data'][url], booru_dict, artists, status)
    return True


def add_danbooru_artists(url, danbooru_artists, booru_dict, db_artists, status):
    artist = next(filter(lambda x: x.booru_search_url == url, db_artists))
    for data in danbooru_artists:
        booru = booru_dict.get(data['id'])
        if booru is None:
            params =\
                {
                    'danbooru_id': data['id'],
                    'name': data['name'],
                    'banned': data['is_banned'],
                    'deleted': data['is_deleted'],
                }
            booru = create_booru_from_parameters(params)
            booru_dict[data['id']] = booru
            inc_dict_entry(status, 'created')
        booru_append_artist(booru, artist)
        inc_dict_entry(status, 'total')


def get_or_create_artist_from_source(site_artist_id, source):
    artist = get_site_artist(site_artist_id, source.SITE.id)
    if artist is None:
        artist = create_artist_from_source(site_artist_id, source)
    return artist


def create_artist_from_source(site_artist_id, source):
    params = source.get_artist_data(site_artist_id)
    if not params['active']:
        return
    return create_artist_from_parameters(params)


def update_artist_from_source(artist):
    source = artist.source
    params = source.get_artist_data(artist.site_artist_id)
    update_artist_from_parameters_standard(artist, params)


def delete_artist(artist, retdata=None):
    """Hard delete. Continue as long as artist record gets deleted."""

    def _delete(artist):
        msg = "[%s]: deleted\n" % artist.shortlink
        delete_record(artist)
        commit_session()
        print(msg)

    retdata = retdata or {'error': False, 'is_deleted': False, 'is_archived': False}
    if not retdata['is_archived'] and artist.illust_count > 0:
        return handle_error_message("Cannot delete artist with existing illusts.", retdata)
    retdata.update(delete_data(artist, _delete))
    if retdata['error']:
        return retdata
    retdata['is_deleted'] = True
    return retdata


def archive_artist_for_deletion(artist, days_to_expire):
    """Soft delete. Preserve data at all costs."""
    retdata = {'error': False, 'is_deleted': False}
    if artist.illust_count > 0:
        return handle_error_message("Cannot delete artist with existing illusts.", retdata)
    retdata.update(save_artist_to_archive(artist, days_to_expire))
    if retdata['error']:
        return retdata
    retdata['is_archived'] = True
    return delete_artist(artist, retdata)


def save_artist_to_archive(artist, days_to_expire):
    retdata = {'error': False}
    archive = get_archive_artist_by_site(artist.site_id, artist.site_artist_id)
    if archive is None:
        archive = create_archive_from_parameters({'days': days_to_expire, 'type_name': 'artist'}, commit=False)
    else:
        update_archive_from_parameters(archive, {'days': days_to_expire}, commit=False)
    retdata['item'] = archive.basic_json()
    archive_params = {k: v for (k, v) in artist.basic_json().items() if k in ArchiveArtist.basic_attributes}
    archive_params['site_account'] = artist.site_account_value
    archive_params['name'] = artist.name_value
    archive_params['profile'] = artist.profile_body
    if archive.artist_data is None:
        archive_params['archive_id'] = archive.id
        archive_artist = ArchiveArtist(**archive_params)
    else:
        archive_artist = archive.artist_data
        archive_artist.update(archive_params)
    archive_artist.webpages_json = [{'url': webpage.url,
                                    'active': webpage.active}
                                    for webpage in artist.webpages]
    archive_artist.site_accounts_json = list(artist.site_account_values)
    archive_artist.names_json = list(artist.name_values)
    archive_artist.profiles_json = list(artist.profile_bodies)
    archive_artist.notations_json = [{'body': notation.body,
                                      'created': notation.created.isoformat(),
                                      'updated': notation.updated.isoformat()}
                                     for notation in artist.notations]
    archive_artist.boorus_json = [booru.danbooru_id for booru in artist.boorus if booru.danbooru_id is not None]
    add_record(archive_artist)
    commit_session()
    return retdata


def recreate_archived_artist(archive):
    artist_data = archive.artist_data
    artist = get_site_artist(artist_data.site_artist_id, artist_data.site_id)
    if artist is not None:
        return handle_error_message(f"Artist already exists: {artist.shortlink}")
    createparams = artist_data.recreate_json()
    swap_key_value(createparams, 'site_account', 'site_account_value')
    swap_key_value(createparams, 'name', 'name_value')
    swap_key_value(createparams, 'profile', 'profile_body')
    artist = create_artist_from_json(createparams, commit=False)
    for webpage_data in artist_data.webpages_json:
        webpage_data['artist_id'] = artist.id
        create_artist_url_from_json(webpage_data, commit=False)
    artist.site_account_values.extend(artist_data.site_accounts_json)
    artist.name_values.extend(artist_data.names_json)
    artist.profile_bodies.extend(artist_data.profiles_json)
    _link_boorus(artist, artist_data)
    for notation in artist_data.notations_json:
        createparams = merge_dicts(notation, {'artist_id': artist.id, 'no_pool': True})
        create_notation_from_json(createparams, commit=False)
    retdata = {'error': False, 'item': artist.to_json()}
    commit_session()
    update_archive_from_parameters(archive, {'days': 7})
    return retdata


def relink_archived_artist(archive):
    artist_data = archive.artist_data
    artist = get_site_artist(artist_data.site_artist_id, artist_data.site_id)
    if artist is None:
        msg = f"{artist_data.site_name} #{artist_data.site_artist_id} not found in artists."
        return handle_error_message(msg)
    retdata = {'error': False, 'item': artist.to_json()}
    _link_boorus(artist, artist_data)
    commit_session()
    return retdata


def artist_delete_site_account(artist, label_id):
    retdata = _relation_params_check(artist, Label, ArtistSiteAccounts, label_id, 'label_id', 'Site account')
    if retdata['error']:
        return retdata
    ArtistSiteAccounts.query.filter_by(artist_id=artist.id, label_id=label_id).delete()
    commit_session()
    return retdata


def artist_swap_site_account(artist, label_id):
    retdata = _relation_params_check(artist, Label, ArtistSiteAccounts, label_id, 'label_id', 'Site account')
    if retdata['error']:
        return retdata
    ArtistSiteAccounts.query.filter_by(artist_id=artist.id, label_id=label_id).delete()
    swap = artist.site_account
    artist.site_account = retdata['attach']
    if swap is not None:
        artist.site_accounts.append(swap)
    commit_session()
    return retdata


def artist_delete_name(artist, label_id):
    retdata = _relation_params_check(artist, Label, ArtistNames, label_id, 'label_id', 'Site account')
    if retdata['error']:
        return retdata
    ArtistNames.query.filter_by(artist_id=artist.id, label_id=label_id).delete()
    commit_session()
    return retdata


def artist_swap_name(artist, label_id):
    retdata = _relation_params_check(artist, Label, ArtistNames, label_id, 'label_id', 'Name')
    if retdata['error']:
        return retdata
    ArtistNames.query.filter_by(artist_id=artist.id, label_id=label_id).delete()
    swap = artist.name
    artist.name = retdata['attach']
    if swap is not None:
        artist.names.append(swap)
    commit_session()
    return retdata


def artist_delete_profile(artist, description_id):
    retdata = _relation_params_check(artist, Description, ArtistProfiles, description_id, 'description_id', 'Profile')
    if retdata['error']:
        return retdata
    ArtistProfiles.query.filter_by(artist_id=artist.id, description_id=description_id).delete()
    commit_session()
    return retdata


def artist_swap_profile(artist, description_id):
    retdata = _relation_params_check(artist, Description, ArtistProfiles, description_id, 'description_id', 'Profile')
    if retdata['error']:
        return retdata
    ArtistProfiles.query.filter_by(artist_id=artist.id, description_id=description_id).delete()
    swap = artist.profile
    artist.profile = retdata['attach']
    if swap is not None:
        artist.profiles.append(swap)
    commit_session()
    return retdata


# ## Private functions

def _relation_params_check(artist, model, m2m_model, model_id, model_field, name):
    retdata = {'error': False}
    attach = model.find(model_id)
    if attach is None:
        return set_error(retdata, "%s #%d does not exist." % (model.model_name, model_id))
    retdata['attach'] = attach
    m2m_row = m2m_model.query.filter_by(**{'artist_id': artist.id, model_field: model_id}).one_or_none()
    if m2m_row is None:
        msg = "%s with %s does not exist on %s." % (name, attach.shortlink, artist.shortlink)
        return set_error(retdata, msg)
    return retdata


def _link_boorus(artist, artist_data):
    if artist_data.boorus is None:
        return
    boorus = get_boorus(artist_data.boorus_json)
    artist.boorus.extend(boorus)
