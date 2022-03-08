# APP/LOGICAL/RECORDS/ARCHIVE_DATA_REC.PY

# ## PYTHON IMPORTS
import os
import logging

# ## PACKAGE IMPORTS
from utility.print import error_print
from utility.file import delete_file

# ## LOCAL IMPORTS
from ..utility import set_error
from ..database.archive_data_db import process_archive_data, ARCHIVE_DATA_DIRECTORY
from .post_rec import reinstantiate_archived_post, relink_archived_post
from .illust_rec import recreate_archived_illust, relink_archived_illust
from .artist_rec import recreate_archived_artist, relink_archived_artist
from .booru_rec import recreate_archived_booru


# ## FUNCTIONS

def reinstantiate_archive_data_item(archive_data):
    # Make these switchers
    retdata = {'error': False}
    data = process_archive_data(archive_data.data)
    if archive_data.type == 'post':
        return reinstantiate_archived_post(data)
    elif archive_data.type == 'illust':
        return recreate_archived_illust(data)
    elif archive_data.type == 'artist':
        return recreate_archived_artist(data)
    elif archive_data.type == 'booru':
        return recreate_archived_booru(data)
    else:
        return set_error(retdata, "Recreating %s not handled yet." % archive_data.type)


def relink_archive_data_item(archive_data):
    # Make these switches
    retdata = {'error': False}
    if archive_data.type == 'post':
        error = relink_archived_post(archive_data.data)
    elif archive_data.type == 'illust':
        error = relink_archived_illust(archive_data.data)
    elif archive_data.type == 'artist':
        error = relink_archived_artist(archive_data.data)
    else:
        return set_error(retdata, "Relinking %s not handled yet." % archive_data.type)
    if error is not None:
        return set_error(retdata, error)
    return retdata


def remove_archive_media_file(archive_data):
    filename = archive_data.data_key + '.' + archive_data.data['body']['file_ext']
    filepath = os.path.join(ARCHIVE_DATA_DIRECTORY, filename)
    try:
        delete_file(filepath)
    except Exception as e:
        logging.error("Error deleting sample.")
        error_print(e)
