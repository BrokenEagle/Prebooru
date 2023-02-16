# APP/LOGICAL/RECORDS/ARCHIVE_REC.PY

# ## PYTHON IMPORTS
import os
import logging

# ## EXTERNAL IMPORTS
from sqlalchemy.ext.associationproxy import ColumnAssociationProxyInstance

# ## PACKAGE IMPORTS
from utility.uprint import exception_print, print_error
from utility.file import delete_file

# ## LOCAL IMPORTS
from ... import SESSION
from ..utility import set_error
from ..database.base_db import record_from_json
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
    except Exception as e:
        return None
    return archive


def recreate_record(model, key, data):
    record = model.find_by_key(key)
    if record is not None:
        raise Exception(f"Record already exists: {record.shortlink}")
    recreate_data = {}
    for rel in model.mandatory_fk_relations:
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
            attr = scalar[2]
        if key not in data['scalars']:
            continue
        for value in data['scalars'][key]:
            getattr(record, attr).append(value)
        if isinstance(scalar, tuple) and len(scalar) > 3:
            scalar[3](record)
    SESSION.flush()


def recreate_attachments(record, data):
    model = record.__class__
    for attr in model.archive_attachments:
        if attr not in data['attachments']:
            continue
        attach_model = getattr(model, attr).property.entity.class_
        reverse_attr = getattr(model, attr).property.back_populates
        for item in data['attachments'][attr]:
            attach_record = attach_model.loads(item)
            SESSION.add(attach_record)
            attach_record.attach(reverse_attr, record)
            SESSION.flush()


def recreate_links(record, data):
    model = record.__class__
    for attr, link_key in model.archive_links:
        if attr not in data['links']:
            continue
        if attr in model.mandatory_fk_relations:
            continue
        link_model = getattr(model, attr).property.entity.class_
        link_attr = getattr(link_model, link_key)
        for value in data['links'][attr]:
            link_record = link_model.query.filter(link_attr == value).one_or_none()
            if link_record is not None:
                getattr(record, attr).append(link_record)
                SESSION.flush()


"""
def recreate_record(data, find_func, create_func, unique_keys, retdata=None):
    retdata = retdata or {}
    unique_values = [data['body'][k] for k in unique_keys]
    record = find_func(*unique_values)
    if record is not None:
        return set_error(retdata, f"Record already exists: {booru.shortlink}"), None
    return retdata, create_func(data['body'])


def recreate_relations(data, record, recreate_func, relation_funcs):
    retdata = retdata or {}
    updateparams = {}
    for key in data['scalars']:
        if len(data['scalars'][key]) == 0:
            continue
        updateparams[key] = data['scalars'][key]
    for key in data['relations']:
        if len(data['relations'][key]) == 0:
            continue
        relation_funcs[key](data['relations'][key], record, updateparams)
    recreate_func(record, updateparams)


def relink_relations(data, record, find_funcs):
    for key in data['links']:
        if len(data['links'][key]) == 0:
            continue
        for unique_key in data['links'][key]:
            item = find_funcs[key](unique_key)
            getattr(record, key).append(item)
            SESSION.flush()
"""

def reinstantiate_archive_item(archive, recreate_func):
    retdata = {'error': False}
    error = recreate_func(archive)
    if error is not None:
        return set_error(retdata, error)
    return retdata


def relink_archive_item(archive, relink_func):
    retdata = {'error': False}
    error = relink_func(archive)
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
