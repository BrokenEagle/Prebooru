# APP/LOGICAL/DATABASE/ARCHIVE_DB.PY

# ## PYTHON IMPORTS
import os
import re

# ## PACKAGE IMPORTS
from config import MEDIA_DIRECTORY
from utility.time import get_current_time, days_from_now

# ## LOCAL IMPORTS
from ...enum_imports import archive_type
from ...models import Archive
from .base_db import set_column_attributes, commit_or_flush, save_record


# ## GLOBAL DATA

ARCHIVE_DIRECTORY = os.path.join(MEDIA_DIRECTORY, 'archive')

ISODATETIME_RG = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')

ANY_WRITABLE_COLUMNS = ['data', 'expires']
NULL_WRITABLE_ATTRIBUTES = ['type_id', 'key', 'media_asset_id']


# ## FUNCTIONS

# #### Create

def create_archive_from_parameters(createparams, commit=True):
    if 'type' in createparams:
        createparams['type_id'] = archive_type.by_name(createparams['type']).id
    return set_archive_from_parameters(Archive(), createparams, commit, 'created')


# #### Update

def update_archive_from_parameters(archive, updateparams, commit=True):
    return set_archive_from_parameters(Archive(), updateparams, commit, 'updated')


# #### Set

def set_archive_from_parameters(archive, setparams, commit, action):
    if 'days' in setparams:
        setparams['expires'] = days_from_now(setparams['days']) if setparams['days'] is not None else None
    if set_column_attributes(archive, ANY_WRITABLE_COLUMNS, NULL_WRITABLE_ATTRIBUTES, setparams):
        save_record(archive, commit, action, safe=True)
    return archive


# #### Delete

def delete_expired_archives():
    total = Archive.query.filter(Archive.expires < get_current_time()).delete()
    commit_or_flush(True)
    return total


# #### Query functions

def get_archive(type, key):
    return Archive.query.enum_join(Archive.type_enum)\
                        .filter(Archive.type_filter('name', '__eq__', type),
                                Archive.key == key)\
                        .one_or_none()


def get_archive_posts_by_md5s(data_keys):
    archives = []
    for i in range(0, len(data_keys), 100):
        sublist = data_keys[i: i + 100]
        archives += Archive.query.enum_join(Archive.type_enum)\
                           .filter(Archive.type_filter('name', '__eq__', 'post'),
                                   Archive.key.in_(sublist))\
                           .all()
    return archives


def get_expired_posts():
    return Archive.query.enum_join(Archive.type_enum)\
                        .filter(Archive.type_filter('name', '__eq__', 'post'),
                                Archive.expires < get_current_time())\
                        .all()


def expired_archive_count():
    return Archive.query.filter(Archive.expires < get_current_time()).get_count()
