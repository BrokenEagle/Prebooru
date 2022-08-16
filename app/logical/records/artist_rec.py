# APP/LOGICAL/RECORDS/ARTIST_REC.PY

# ## PACKAGE IMPORTS
from utility.print import exception_print

# ## LOCAL IMPORTS
from ... import SESSION
from ..utility import set_error
from ..database.artist_db import create_artist_from_parameters, update_artist_from_parameters, get_site_artist,\
    create_artist_from_raw_parameters, artist_append_booru, delete_artist
from ..database.booru_db import get_booru
from ..database.notation_db import create_notation_from_raw_parameters
from ..database.archive_db import get_archive_data, create_archive_data, update_archive_data


# ## FUNCTIONS

def create_artist_from_source(site_artist_id, source):
    params = source.get_artist_data(site_artist_id)
    if not params['active']:
        return
    return create_artist_from_parameters(params)


def update_artist_from_source(artist, source):
    params = source.get_artist_data(artist.site_artist_id)
    if params['active']:
        # These are only removable through the HTML/JSON UPDATE routes
        params['webpages'] += ['-' + w.url for w in artist.webpages if w.url not in params['webpages']]
        params['names'] += [name for name in artist.names if name not in params['names']]
        params['site_accounts'] += [name for name in artist.site_accounts if name not in params['site_accounts']]
    update_artist_from_parameters(artist, params)


def archive_artist_for_deletion(artist):
    retdata = {'error': False}
    retdata = _archive_artist_data(artist, retdata)
    if retdata['error']:
        return retdata
    return _delete_artist_data(artist, retdata)


def recreate_archived_artist(data):
    retdata = {'error': False}
    artist_data = data['body']
    artist = get_site_artist(artist_data['site_artist_id'], artist_data['site_id'])
    if artist is not None:
        return set_error(retdata, "Artist already exists: artist #%d" % artist.id)
    if len(data['scalars']['names']):
        artist_data['names'] = data['scalars']['names']
    if len(data['scalars']['site_accounts']):
        artist_data['site_accounts'] = data['scalars']['site_accounts']
    if len(data['scalars']['profiles']):
        artist_data['profiles'] = data['scalars']['profiles']
    if len(data['relations']['webpages']):
        artist_data['webpages'] = [('' if webpage['active'] else '-') + webpage['url']
                                   for webpage in data['relations']['webpages']]
    try:
        artist = create_artist_from_raw_parameters(data['body'])
    except Exception as e:
        exception_print(e)
        return set_error(retdata, "Error creating artist: %s" % repr(e))
    retdata['item'] = artist.to_json()
    relink_archived_artist(data, artist)
    for notation_data in data['relations']['notations']:
        notation = create_notation_from_raw_parameters(notation_data)
        artist.notations.append(notation)
        SESSION.commit()
    return retdata


def relink_archived_artist(data, artist=None):
    if artist is None:
        artist = get_site_artist(data['body']['site_artist_id'], data['body']['site_id'])
        if artist is None:
            return "No artist found with site ID %d" % data['body']['site_artist_id']
    for danbooru_id in data['links']['boorus']:
        booru = get_booru(danbooru_id)
        if booru is None:
            return
        artist_append_booru(artist, booru)


# #### Private functions

def _archive_artist_data(artist, retdata):
    data = {
        'body': artist.archive_dict(),
        'scalars': {
            'profiles': list(artist.profiles),
            'names': list(artist.names),
            'site_accounts': list(artist.site_accounts),
        },
        'relations': {
            'webpages': [webpage.archive_dict() for webpage in artist.webpages],
            'notations': [notation.archive_dict() for notation in artist.notations],
        },
        'links': {
            'boorus': [booru.danbooru_id for booru in artist.boorus],
        },
    }
    data_key = '%d-%d' % (artist.site_id, artist.site_artist_id)
    archive_data = get_archive_data('artist', data_key)
    try:
        if archive_data is None:
            create_archive_data('artist', data_key, data, 30)
        else:
            update_archive_data(archive_data, data, 30)
    except Exception as e:
        return set_error(retdata, "Error archiving data: %s" % str(e))
    return retdata


def _delete_artist_data(artist, retdata):
    try:
        delete_artist(artist)
    except Exception as e:
        SESSION.rollback()
        return set_error(retdata, "Error deleting artist: %s" % str(e))
    return retdata
