# APP/LOGICAL/DATABASE/ARCHIVE_DB.PY

# ## PYTHON IMPORTS
import os
import re

# ## PACKAGE IMPORTS
from config import MEDIA_DIRECTORY
from utility.time import get_current_time, days_from_now

# ## LOCAL IMPORTS
from ... import SESSION
from ...models import Archive


# ## GLOBAL DATA

ARCHIVE_DIRECTORY = os.path.join(MEDIA_DIRECTORY, 'archive')

ISODATETIME_RG = re.compile(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')


# ## FUNCTIONS

# ###### CREATE

def create_archive(type, key, data, days):
    data = {
        'type': type,
        'key': key,
        'data': data,
        'expires': days_from_now(days) if days is not None else None,
    }
    archive_item = Archive(**data)
    SESSION.add(archive_item)
    SESSION.commit()
    return archive_item


# ###### UPDATE

def update_archive(archive, data, days):
    archive.data = data
    archive.expires = days_from_now(days) if days is not None else None
    SESSION.commit()


def set_archive_permenant(item):
    item.expires = None
    SESSION.commit()


def set_archive_temporary(item, days):
    item.expires = days_from_now(days)
    SESSION.commit()


# ###### DELETE

def delete_expired_archive():
    from ..records.archive_rec import remove_archive_media_file
    Archive.query.filter(Archive.type_id != 'post', Archive.expires < get_current_time()).delete()
    SESSION.commit()
    expired_data = Archive.query.filter(Archive.type_id == 'post', Archive.expires < get_current_time()).all()
    if len(expired_data) == 0:
        return
    for archive in expired_data:
        remove_archive_media_file(archive)
    Archive.query.filter(Archive.id.in_([data.id for data in expired_data])).delete()
    SESSION.commit()


# #### Query functions

def get_archive(type, key):
    return Archive.query.filter_by(type_id=type.value, key=key).one_or_none()


def get_archive_posts_by_md5s(data_keys):
    archives = []
    for i in range(0, len(data_keys), 100):
        sublist = data_keys[i: i + 100]
        archives += Archive.query.filter(Archive.type_filter('name', '__eq__', 'post'), Archive.key.in_(sublist)).all()
    return archives


def expired_archive_count():
    return Archive.query.filter(Archive.expires < get_current_time()).get_count()
