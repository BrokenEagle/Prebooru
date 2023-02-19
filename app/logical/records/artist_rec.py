# APP/LOGICAL/RECORDS/ARTIST_REC.PY

# ## PYTHON IMPORTS
import itertools

# ## PACKAGE IMPORTS
from utility.data import inc_dict_entry

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Artist
from ..logger import handle_error_message
from ..database.artist_db import create_artist_from_parameters, update_artist_from_parameters, get_site_artist,\
    delete_artist, get_artists_without_boorus_page
from ..database.booru_db import get_boorus, create_booru_from_parameters, booru_append_artist
from ..database.archive_db import set_archive_temporary
from .base_rec import delete_data
from .archive_rec import archive_record, recreate_record, recreate_scalars, recreate_attachments, recreate_links


# ## FUNCTIONS

def check_all_artists_for_boorus():
    print("Checking all artists for Danbooru artists.")
    status = {'total': 0, 'created': 0}
    page = get_artists_without_boorus_page(100)
    booru_dict = {}
    while True:
        print(f"check_all_artists_for_boorus: {page.first} - {page.last} / Total({page.count})")
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
                    'current_name': data['name'],
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
    source = artist.site.source
    params = source.get_artist_data(artist.site_artist_id)
    if params['active']:
        # These are only removable through the HTML/JSON UPDATE routes
        params['webpages'] += ['-' + w.url for w in artist.webpages if w.url not in params['webpages']]
        params['names'] += [name for name in artist.names if name not in params['names']]
        params['site_accounts'] += [name for name in artist.site_accounts if name not in params['site_accounts']]
    update_artist_from_parameters(artist, params)


def archive_artist_for_deletion(artist, expires=30):
    archive = archive_record(artist, expires)
    if archive is None:
        return handle_error_message(f"Error archiving data [{artist.shortlink}].")
    retdata = {'item': archive.to_json()}
    retdata.update(delete_data(artist, delete_artist))
    return retdata


def recreate_archived_artist(archive):
    try:
        artist = recreate_record(Artist, archive.key, archive.data)
        recreate_scalars(artist, archive.data)
        recreate_attachments(artist, archive.data)
        recreate_links(artist, archive.data)
    except Exception as e:
        retdata = handle_error_message(str(e))
        SESSION.rollback()
    else:
        retdata = {'error': False, 'item': artist.to_json()}
        set_archive_temporary(archive, 7)
        SESSION.commit()
    return retdata


def relink_archived_artist(archive):
    artist = Artist.find_by_key(archive.key)
    if artist is None:
        return f"No artist found with key {archive.key}"
    recreate_links(artist, archive.data)
