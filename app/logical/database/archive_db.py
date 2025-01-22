# APP/LOGICAL/DATABASE/ARCHIVE_DB.PY

# ## PYTHON IMPORTS
import os
import re

# ## PACKAGE IMPORTS
from config import MEDIA_DIRECTORY
from utility.time import get_current_time, days_from_now

# ## LOCAL IMPORTS
from ...models import Archive, ArchiveType
from .base_db import add_record, commit_session, commit_or_flush


# ## GLOBAL DATA

ARCHIVE_DIRECTORY = os.path.join(MEDIA_DIRECTORY, 'archive')

ISODATETIME_RG = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')


# ## FUNCTIONS

# ###### CREATE

def create_archive(type_name, key, data, days):
    data = {
        'type_id': ArchiveType.to_id(type_name),
        'key': key,
        'data': data,
        'expires': days_from_now(days) if days is not None else None,
    }
    archive_item = Archive(**data)
    add_record(archive_item)
    commit_session()
    return archive_item


# ###### UPDATE

def update_archive(archive, data, days):
    archive.data = data
    archive.expires = days_from_now(days) if days is not None else None
    commit_session()


def set_archive_permenant(item):
    item.expires = None
    commit_session()


def set_archive_temporary(item, days, commit=False):
    item.expires = days_from_now(days)
    commit_or_flush(commit)


# #### Query functions

def get_archive(type_name, key):
    return Archive.query.filter(Archive.type_value == type_name, Archive.key == key).one_or_none()


def get_archive_posts_by_md5s(data_keys):
    archives = []
    for i in range(0, len(data_keys), 100):
        sublist = data_keys[i: i + 100]
        archives += Archive.query.filter(Archive.type_value == 'post', Archive.key.in_(sublist)).all()
    return archives


def expired_archive_count():
    return Archive.query.filter(Archive.expires < get_current_time()).get_count()
