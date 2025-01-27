# APP/LOGICAL/RECORDS/ARCHIVE_REC.PY

# ## PYTHON IMPORTS
import os
import logging

# ## PACKAGE IMPORTS
from utility.uprint import exception_print
from utility.file import delete_file
from utility.time import get_current_time

# ## LOCAL IMPORTS
from ...models import Archive
from ..database.base_db import record_from_json, add_record, commit_session, flush_session
from ..database.archive_db import ARCHIVE_DIRECTORY, get_archive, create_archive, update_archive


# ## FUNCTIONS

def archive_record(record, expires=None):
    data = record.archive()
    data_key = record.key
    model_name = record.model_name
    archive = get_archive(model_name, data_key)
    try:
        if archive is None:
            archive = create_archive(model_name, data_key, data, expires)
        else:
            update_archive(archive, data, expires)
    except Exception:
        return None
    return archive


def recreate_record(model, key, data):
    record = model.find_by_key(key)
    if record is not None:
        raise Exception(f"Record already exists: {record.shortlink}")
    recreate_data = {}
    for rel in model.mandatory_links:
        if rel not in data['links']:
            raise Exception(f"Mandatory link to {rel} not found in archive data.")
        value = data['links'][rel]
        rel_record = model.find_rel_by_key(rel, key, value)
        if rel_record is None:
            raise Exception(f"Mandatory link to {rel} using key {value} not found in database.")
        relcol = next(iter(getattr(model, rel).property.local_columns))
        recreate_data[relcol.key] = rel_record.id
    for attr in data['body']:
        mapping = next((incl for incl in model.archive_includes if incl[0] == attr), None)
        if mapping is not None:
            key, field = mapping
        else:
            key, field = attr, attr
        recreate_data[field] = data['body'][key]
    return record_from_json(model, recreate_data)


def recreate_scalars(record, data):
    model = record.__class__
    for scalar in model.archive_scalars:
        if isinstance(scalar, str):
            key = scalar
            attr = scalar
        elif isinstance(scalar, tuple):
            key = scalar[0]
            attr = scalar[1]
        if key not in data['scalars']:
            continue
        for value in data['scalars'][key]:
            getattr(record, attr).append(value)
    flush_session()


def recreate_attachments(record, data):
    model = record.__class__
    for attachment in model.archive_attachments:
        if isinstance(attachment, tuple):
            key, attr, *args = attachment
        else:
            key, attr, *args = attachment, attachment
        if key not in data['attachments']:
            continue
        if len(args):
            attach_model = getattr(record, args[0])
        else:
            attach_model = getattr(model, attr).property.entity.class_
        reverse_attr = getattr(model, attr).property.back_populates
        attachments = data['attachments'][key]
        if attachments is None:
            continue
        attachments = [attachments] if isinstance(attachments, dict) else attachments
        for item in attachments:
            attach_record = attach_model.loads(item, record)
            add_record(attach_record)
            attach_record.attach(reverse_attr, record)
            flush_session()


def recreate_links(record, data):
    model = record.__class__
    for attr, link_key, *args in model.archive_links:
        if attr not in data['links']:
            continue
        if attr in model.mandatory_links:
            continue
        if len(args) == 2:
            link_func = getattr(record, args[1])
            for value in data['links'][attr]:
                if link_func(value):
                    flush_session()
            continue
        link_model = getattr(model, attr).property.entity.class_
        for value in data['links'][attr]:
            if isinstance(value, dict):
                value = value[link_key]
            link_record = link_model.find_by_key(value)
            if link_record is not None:
                getattr(record, attr).append(link_record)
                flush_session()


def remove_archive_media_file(archive):
    filename = archive.key + '.' + archive.data['body']['file_ext']
    filepath = os.path.join(ARCHIVE_DIRECTORY, filename)
    try:
        delete_file(filepath)
    except Exception as e:
        logging.error("Error deleting sample.")
        exception_print(e)


def delete_expired_archive():
    status = {}
    status['nonposts'] = Archive.query.filter(Archive.type_value != 'post',
                                              Archive.expires < get_current_time())\
                                      .delete()
    commit_session()
    expired_data = Archive.query.filter(Archive.type_value == 'post', Archive.expires < get_current_time()).all()
    status['posts'] = len(expired_data)
    if len(expired_data) > 0:
        for archive in expired_data:
            remove_archive_media_file(archive)
        Archive.query.filter(Archive.id.in_([data.id for data in expired_data])).delete()
        commit_session()
    return status
