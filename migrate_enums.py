# MIGRATE_ENUMS.PY

# ## PYTHON IMPORTS
import os
import uuid
import functools
import colorama
from argparse import ArgumentParser

# ## EXTERNAL IMPORTS
from sqlalchemy import text, func
from sqlalchemy.sql import case, label, union_all

# ## PACKAGE IMPORTS
from utility.uprint import print_info, print_warning, print_error
from utility.file import create_directory, get_directory_listing, put_get_json, put_get_raw
from utility.data import merge_dicts


# ## FUNCTIONS

# #### Initialize functions

def initialize_enums_config():
    global ENUMS_CONFIG, SESSION
    from app import SESSION
    from app.models.model_enums import SiteDescriptor, ApiDataType, ArchiveType, PostType, SubscriptionStatus,\
        SubscriptionElementStatus, SubscriptionElementKeep, UploadStatus, DownloadStatus, DownloadElementStatus,\
        PoolElementType, TagType
    from app.models import ApiData, Archive, Artist, Illust, IllustUrl, PoolElement, Post, Subscription,\
        SubscriptionElement, Upload, Download, DownloadElement, Tag
    ENUMS_CONFIG = [
        {
            'model': ApiDataType,
            'tables': [{
                'table': ApiData,
                'field': 'type_id',
            }],
        }, {
            'model': ArchiveType,
            'tables': [{
                'table': Archive,
                'field': 'type_id',
            }],
        }, {
            'model': PostType,
            'tables': [{
                'table': Post,
                'field': 'type_id',
            }],
        }, {
            'model': SubscriptionStatus,
            'tables': [{
                'table': Subscription,
                'field': 'status_id',
            }],
        }, {
            'model': SubscriptionElementStatus,
            'tables': [{
                'table': SubscriptionElement,
                'field': 'status_id',
            }],
        }, {
            'model': SubscriptionElementKeep,
            'tables': [{
                'table': SubscriptionElement,
                'field': 'keep_id',
            }],
        }, {
            'model': UploadStatus,
            'tables': [{
                'table': Upload,
                'field': 'status_id',
            }],
        }, {
            'model': DownloadStatus,
            'tables': [{
                'table': Download,
                'field': 'status_id',
            }],
        }, {
            'model': DownloadElementStatus,
            'tables': [{
                'table': DownloadElement,
                'field': 'status_id',
            }],
        }, {
            'model': PoolElementType,
            'tables': [{
                'table': PoolElement,
                'field': 'type_id',
            }],
        }, {
            'model': TagType,
            'tables': [{
                'table': Tag,
                'field': 'type_id',
            }],
        }, {
            'model': SiteDescriptor,
            'tables': [{
                'table': ApiData,
                'field': 'site_id',
            }, {
                'table': Artist,
                'field': 'site_id',
            }, {
                'table': Illust,
                'field': 'site_id',
            }, {
                'table': IllustUrl,
                'field': 'site_id',
            }, {
                'table': IllustUrl,
                'field': 'sample_site_id',
            }],
        },
    ]


# #### Order functions

def get_value_counts_single(model, model_id):
    column_attr = getattr(model, model_id)
    return model.query.filter(column_attr.is_not(None)).group_by(column_attr)\
                      .with_entities(column_attr, func.count(column_attr))\
                      .all()


def get_value_counts_multi(model_groups):
    unique_column = 'unique_id'
    unions = []
    for model_group in model_groups:
        model, model_id = model_group
        column_attr = getattr(model, model_id)
        label_attr = label(unique_column, column_attr)
        unions.append(model.query.filter(label_attr.is_not(None)).with_entities(label_attr))
    unique_cte = union_all(*unions).cte('unique_ids')
    unique_attr = getattr(unique_cte.columns, unique_column)
    return SESSION.query(unique_cte).group_by(unique_attr)\
                  .with_entities(unique_attr.label('unique_id'), func.count(unique_attr).label('cnt'))\
                  .all()


# #### Migrate functions

def populate_tables(config, reorder_map):
    model = config['model']
    model.query.delete()
    inserts = [model(id=v, name=k) for (k, v) in reorder_map.items()]
    SESSION.bulk_save_objects(inserts)
    SESSION.flush()


def migrate_tables(config, reorder_map):
    update_map = {model.to_id(k): v for (k, v) in reorder_map.items()}
    for table_config in config['tables']:
        table = table_config['table']
        field = table_config['field']
        field_attr = getattr(table, field)
        table.query.update({field: case(update_map, value=field_attr)})
    SESSION.flush()


def order_by_default(config):
    model = config['model']
    if model.mapping.needs_upgrade:
        print_warning("Mismatching values! Run an upgrade first.")
        return
    default_map = model.mapping._default_map
    if all(model.to_id(k) == v for (k, v) in default_map.items()):
        print_info("Table already has default order!")
        return
    try:
        SESSION.execute(text("PRAGMA foreign_keys = 0"))
        populate_tables(config, default_map)
        migrate_tables(config, default_map)
        SESSION.execute(text("PRAGMA foreign_keys = 1"))
    except Exception as e:
        print_error("Exception:", e)
        SESSION.rollback()
    else:
        SESSION.commit()
    model.load()
    SESSION.remove()


def order_by_count(config):
    model = config['model']
    if model.mapping.needs_upgrade:
        print_warning("Mismatching values! Run an upgrade first.")
        return
    if len(config['tables']) == 1:
        counts = get_value_counts_single(config['tables'][0]['table'], config['tables'][0]['field'])
    else:
        counts = get_value_counts_multi([(subconfig['table'], subconfig['field']) for subconfig in config['tables']])
    counts = [count for count in counts if count[0] not in model.__mandatory_mapping__.values()]
    for name in model.__initial_mapping__:
        id = model.__initial_mapping__[name]
        if not any(c for c in counts if c[0] == id):
            counts.append((id, 0))
    counts = sorted(counts, key=lambda x: x[1], reverse=True)
    count_map = merge_dicts({model.to_name(c[0]): i for (i, c) in enumerate(counts)}, model.__mandatory_mapping__)
    if all(model.to_id(k) == v for (k, v) in count_map.items()):
        print_info("Table already ordered by count!")
        return
    try:
        SESSION.execute(text("PRAGMA foreign_keys = 0"))
        populate_tables(config, count_map)
        migrate_tables(config, count_map)
        SESSION.execute(text("PRAGMA foreign_keys = 1"))
    except Exception as e:
        print_error("Exception:", e,)
        SESSION.rollback()
    else:
        SESSION.commit()
    model.load()


# #### Upgrade functions

def upgrade_table(config):
    model = config['model']
    if model.is_empty:
        print_info("Populating empty table.")
        populate_tables(config, model.mapping._default_map)
        SESSION.commit()
        return
    if not model.mapping.needs_upgrade:
        print_warning("Table does not need to be upgraded.")
        return
    added_names = set(model.mapping._default_map.keys()).difference(model.mapping._name_map.keys())
    if len(added_names) > 0:
        print("Adding values to enum table.")
        used_ids = set(model.mapping._id_map.keys())
        for name in added_names:
            if name in model.mapping._mandatory_map:
                insert = model(id=model.mapping._mandatory_map[name], name=name)
            else:
                next_id = next(i for i in range(255) if i not in used_ids)
                insert = model(id=next_id, name=name)
            SESSION.add(insert)
        SESSION.commit()
        model.load()
    removed_names = set(model.mapping._name_map.keys()).difference(model.mapping._default_map.keys())
    if len(removed_names) > 0:
        print("Setting removed enum values to unknown.")
        ids = [model.to_id(name) for name in removed_names]
        for table_config in config['tables']:
            table = table_config['table']
            field = table_config['field']
            field_attr = getattr(table, field)
            unknown_val = model.to_id('unknown')
            model.query.filter(field_attr.in_(ids)).update({field: unknown_val})
        SESSION.commit()


# #### Main execution functions

def reorder_tables(args):
    if args.default:
        reorder_func = order_by_default
    elif args.count:
        reorder_func = order_by_count
    else:
        print("Must specify default or count order with '--default' or '--count' respectively.")
        exit(-1)
    initialize_enums_config()
    if args.table:
        config = next((c for c in ENUMS_CONFIG if c['model']._table_name() == args.table), None)
        if config is None:
            print("Enum table not found!")
            exit(-1)
        print("Migrating enums table:", args.table)
        reorder_func(config)
    else:
        for config in ENUMS_CONFIG:
            print("Migrating enums table:", config['model']._table_name())
            reorder_func(config)
    print("Done!")


def upgrade_tables(args):
    initialize_enums_config()
    if args.table:
        config = next((c for c in ENUMS_CONFIG if c['model']._table_name() == args.table), None)
        if config is None:
            print_warning("Enum table not found!")
            exit(-1)
        upgrade_table(config)
    else:
        for config in ENUMS_CONFIG:
            print("Upgrading enums table:", config['model']._table_name())
            upgrade_table(config)
    print("Done!")


def main(args):
    colorama.init(autoreset=True)
    if args.action == 'reorder':
        reorder_tables(args)
    elif args.action == 'upgrade':
        upgrade_tables(args)


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to load/modify enum and dependant tables.")
    parser.add_argument('action', choices=['reorder', 'upgrade'], help="Choose which action to perform.")
    parser.add_argument('--default', required=False, action="store_true", default=False)
    parser.add_argument('--count', required=False, action="store_true", default=False)
    parser.add_argument('--table', required=False, type=str)
    args = parser.parse_args()

    main(args)
