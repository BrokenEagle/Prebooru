# APP/LOGICAL/RECORDS/ARCHIVE_REC.PY

# ## PYTHON IMPORTS
import os
import logging

# ## PACKAGE IMPORTS
from utility.uprint import exception_print
from utility.file import delete_file

# ## LOCAL IMPORTS
from ..utility import set_error
from ..database.archive_db import ARCHIVE_DIRECTORY
from .post_rec import recreate_archived_post, relink_archived_post
from .illust_rec import recreate_archived_illust, relink_archived_illust
from .artist_rec import recreate_archived_artist, relink_archived_artist
from .booru_rec import recreate_archived_booru


# ## FUNCTIONS

def reinstantiate_archive_item(archive):
    # Make these switchers
    retdata = {'error': False}
    if archive.type.name == 'post':
        return recreate_archived_post(archive, True)
    elif archive.type.name == 'illust':
        return recreate_archived_illust(archive.data)
    elif archive.type.name == 'artist':
        return recreate_archived_artist(archive.data)
    elif archive.type.name == 'booru':
        return recreate_archived_booru(archive.data)
    else:
        return set_error(retdata, "Recreating %s not handled yet." % archive.type.name)


def relink_archive_item(archive):
    # Make these switches
    retdata = {'error': False}
    if archive.type.name == 'post':
        error = relink_archived_post(archive)
    elif archive.type.name == 'illust':
        error = relink_archived_illust(archive.data)
    elif archive.type.name == 'artist':
        error = relink_archived_artist(archive.data)
    else:
        return set_error(retdata, "Relinking %s not handled yet." % archive.type.name)
    if error is not None:
        return set_error(retdata, error)
    return retdata


def remove_archive_media_file(archive):
    filename = archive.key + '.' + archive.data['body']['file_ext']
    filepath = os.path.join(ARCHIVE_DIRECTORY, filename)
    try:
        delete_file(filepath)
    except Exception as e:
        logging.error("Error deleting sample.")
        exception_print(e)
