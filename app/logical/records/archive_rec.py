# APP/LOGICAL/RECORDS/ARCHIVE_REC.PY

# ## PYTHON IMPORTS
import os
import logging

# ## PACKAGE IMPORTS
from utility.uprint import exception_print
from utility.file import delete_file

# ## LOCAL IMPORTS
from ... import SESSION
from ..database.base_db import record_from_json
from ..database.archive_db import ARCHIVE_DIRECTORY, get_archive, create_archive_from_parameters,\
    update_archive_from_parameters


# ## FUNCTIONS

def archive_record(record, days, commit=True):
    model_name = record.model_name
    key = record.key
    archive = get_archive(model_name, key)
    if archive is None:
        parameters = {
            'type': model_name,
            'key': key,
            'data': record.archive(),
            'days': days,
        }
        if model_name == 'post':
            parameters['media_asset_id'] = post.media_asset_id
        return create_archive_from_parameters(parameters, commit)
    return update_archive_from_parameters(archive, {'data': record.archive(), 'days': days}, commit)


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
        attachments = [attachments] if isinstance(attachments, dict) else attachments
        for item in attachments:
            attach_record = attach_model.loads(item, record)
            SESSION.add(attach_record)
            attach_record.attach(reverse_attr, record)
            SESSION.flush()


def recreate_links(record, data):
    model = record.__class__
    for attr, link_key, *args in model.archive_links:
        if attr not in data['links']:
            continue
        if attr in model.mandatory_fk_relations:
            continue
        if len(args) == 2:
            link_func = getattr(record, args[1])
            for value in data['links'][attr]:
                if link_func(value):
                    SESSION.flush()
            continue
        link_model = getattr(model, attr).property.entity.class_
        for value in data['links'][attr]:
            if isinstance(value, dict):
                value = value[link_key]
            link_record = link_model.find_by_key(value)
            if link_record is not None:
                getattr(record, attr).append(link_record)
                SESSION.flush()
