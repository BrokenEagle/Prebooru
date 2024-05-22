# APP/LOGICAL/RECORDS/ILLUST_REC.PY

# ## PACKAGE IMPORTS
from utility.uprint import print_warning

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Illust
from ..logger import handle_error_message
from ..database.artist_db import get_blank_artist
from ..database.illust_db import create_illust_from_parameters, update_illust_from_parameters, delete_illust
from ..database.archive_db import update_archive_from_parameters
from .base_rec import delete_data
from .artist_rec import get_or_create_artist_from_source
from .archive_rec import archive_record, recreate_record, recreate_scalars, recreate_attachments, recreate_links


# ## FUNCTIONS

def create_illust_from_source(site_illust_id, source):
    createparams = source.get_illust_data(site_illust_id)
    if not createparams['active']:
        return
    artist = get_or_create_artist_from_source(createparams['site_artist_id'], source)
    if artist is None:
        return
    createparams['artist_id'] = artist.id
    return create_illust_from_parameters(createparams)


def update_illust_from_source(illust):
    source = illust.site.source
    updateparams = source.get_illust_data(illust.site_illust_id)
    if updateparams['active']:
        # These are only removable through the HTML/JSON UPDATE routes
        updateparams['tags'] += [tag for tag in illust.tags if tag not in updateparams['tags']]
    update_illust_from_parameters(illust, updateparams)
    if 'site_artist_id' in updateparams and illust.artist.site_artist_id != updateparams['site_artist_id']:
        artist = get_or_create_artist_from_source(updateparams['site_artist_id'], source)
        if artist is None:
            artist = get_blank_artist()
        print_warning(f"[{illust.shortlink}] Switching artist from {illust.artist.shortlink} to {artist.shortlink}")
        illust.artist = artist
        SESSION.commit()


def archive_illust_for_deletion(illust, expires=30):
    archive = archive_record(illust, expires)
    if archive is None:
        return handle_error_message(f"Error archiving data [{illust.shortlink}].")
    retdata = {'item': archive.to_json()}
    retdata.update(delete_data(illust, delete_illust))
    return retdata


def recreate_archived_illust(archive):
    try:
        illust = recreate_record(Illust, archive.key, archive.data)
        recreate_scalars(illust, archive.data)
        recreate_attachments(illust, archive.data)
        recreate_links(illust, archive.data)
    except Exception as e:
        retdata = handle_error_message(str(e))
        SESSION.rollback()
    else:
        retdata = {'error': False, 'item': illust.to_json()}
        update_archive_from_parameters(archive, {'days': 7})
    return retdata


def relink_archived_illust(archive):
    illust = Illust.find_by_key(archive.key)
    if illust is None:
        return f"No illust found with key {archive.key}"
    recreate_links(illust, archive.data)
