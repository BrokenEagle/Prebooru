# APP/LOGICAL/RECORDS/ARCHIVE_REC.PY

# ## PYTHON IMPORTS
import os
import logging

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
    for field in data['body']:
        if field in model.recreate_mapping:
            mapping = model.recreate_mapping[field]
            if isinstance(mapping, str):
                recreate_data[mapping] = data['body'][field]
            elif isinstance(mapping, tuple):
                name, mapper = mapping
                recreate_data[name] = mapper(data['body'][field])
        else:
            recreate_data[field] = data['body'][field]
    record = record_from_json(model, recreate_data)
    return record


def recreate_scalars(record, data):
    model = record.__class__
    for scalar in data['scalars']:
        if scalar not in model.scalar_relationships:
            continue
        scalar_config = model.scalar_relationships[scalar]
        if len(scalar_config) == 3:
            attr, scalar_attr, mapper = scalar_config
        elif len(scalar_config) == 2:
            attr, scalar_attr = scalar_config
            mapper = lambda x: x
        scalar_model = getattr(model, attr).property.entity.class_
        for value in data['scalars'][scalar]:
            append_record = scalar_model.query.filter(getattr(scalar_model, scalar_attr) == value).one_or_none()
            if append_record is None:
                append_record = record_from_json(scalar_model, {scalar_attr: value})
            getattr(record, attr).append(append_record)
            SESSION.flush()



def recreate_attachments(model, data):
    for attribute, scalar_key, scalar_model in model.scalar_relationships:
        data_key = attribute.strip('_')
        for value in data['scalars'][data_key]:
            append_record = scalar_model.query.filter(getattr(scalar_model, scalar_key) == value).one_or_none()
            if append_record is None:
                append_record = scalar_model.from_json({scalar_key: value})
            getattr(record, attribute).append(append_record)
            SESSION.flush()
    table_name = model._table_name()
    for attribute, attach_model in attach_relationships:
        for item in data['relations'][attribute]:
            attach_record = attach_model.loads(item)
            setattr(attach_record, table_name, record)
            SESSION.flush()
    for attribute, link_key in link_relationships:
        link_model = getattr(model, attribute).property.entity.class_
        link_record = link_model.query.filter(getattr(link_model, link_key)).one_or_none()
        if link_record is not None:
            getattr(record, attribute).append(link_record)
            SESSION.flush()
    SESSION.commit()
    return record

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
