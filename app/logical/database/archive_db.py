# APP/LOGICAL/DATABASE/ARCHIVE_DB.PY

# ## PYTHON IMPORTS
import os
import re

# ## PACKAGE IMPORTS
from config import MEDIA_DIRECTORY
from utility.time import get_current_time, days_from_now

# ## LOCAL IMPORTS
from ...models import Archive
from .base_db import add_record, commit_session, commit_or_flush


# ## GLOBAL DATA

ARCHIVE_DIRECTORY = os.path.join(MEDIA_DIRECTORY, 'archive')

ISODATETIME_RG = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')


# ## FUNCTIONS

# ###### CREATE

def create_archive(type, key, data, days):
    data = {
        'type_id': Archive.type_enum.by_name(type).id,
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


# ###### DELETE

def delete_expired_archive():
    from ..records.archive_rec import remove_archive_media_file
    status = {}
    status['nonposts'] =\
        Archive.query.enum_join(Archive.type_enum)\
               .filter(Archive.type_filter('name', '__ne__', 'post'),
                       Archive.expires < get_current_time())\
               .delete()
    commit_session()
    expired_data = Archive.query.enum_join(Archive.type_enum)\
                                .filter(Archive.type_filter('name', '__eq__', 'post'),
                                        Archive.expires < get_current_time())\
                                .all()
    status['posts'] = len(expired_data)
    if len(expired_data) > 0:
        for archive in expired_data:
            remove_archive_media_file(archive)
        Archive.query.filter(Archive.id.in_([data.id for data in expired_data])).delete()
        commit_session()
    return status


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


def expired_archive_count():
    return Archive.query.filter(Archive.expires < get_current_time()).get_count()
