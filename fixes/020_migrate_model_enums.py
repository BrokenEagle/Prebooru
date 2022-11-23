# FIXES/020_INITIALIZE_DUPLICATE_POOL_ELEMENTS.PY

# ## PYTHON IMPORTS
import os
import sys
import uuid
from argparse import ArgumentParser

# ## EXTERNAL IMPORTS
from sqlalchemy import text
from sqlalchemy.sql.expression import case
from mako.template import Template


# ## FUNCTIONS

# #### Auxiliary functions

def initialize(args):
    global SESSION, ENUMS_CONFIG, Version, create_directory, get_directory_listing, put_get_json, put_get_raw
    sys.path.append(os.path.abspath('.'))
    from app import SESSION
    if args.local:
        from app import local_enums as enums
    else:
        from app import default_enums as enums
    from utility.file import create_directory, get_directory_listing, put_get_json, put_get_raw
    from app.models.model_enums import SiteDescriptor, ApiDataType, ArchiveType, PostType, SubscriptionStatus,\
        SubscriptionElementStatus, SubscriptionElementKeep, UploadStatus, UploadElementStatus, PoolElementType,\
        SiteDataType, TagType
    from app.models import ApiData, Archive, Artist, Illust, IllustUrl, PoolElement, Post, SiteData,\
        Subscription, SubscriptionElement, Upload, UploadElement, Tag, Version
    ENUMS_CONFIG = [
        {
            'model': ApiDataType,
            'enum': enums.ApiDataTypeEnum,
            'tables': [{
                'table': ApiData,
                'field': 'type',
            }],
        }, {
            'model': ArchiveType,
            'enum': enums.ArchiveTypeEnum,
            'tables': [{
                'table': Archive,
                'field': 'type',
            }],
        }, {
            'model': PostType,
            'enum': enums.PostTypeEnum,
            'tables': [{
                'table': Post,
                'field': 'type',
            }],
        }, {
            'model': SubscriptionStatus,
            'enum': enums.SubscriptionStatusEnum,
            'tables': [{
                'table': Subscription,
                'field': 'status',
            }],
        }, {
            'model': SubscriptionElementStatus,
            'enum': enums.SubscriptionElementStatusEnum,
            'tables': [{
                'table': SubscriptionElement,
                'field': 'status',
            }],
        }, {
            'model': SubscriptionElementKeep,
            'enum': enums.SubscriptionElementKeepEnum,
            'tables': [{
                'table': SubscriptionElement,
                'field': 'keep',
            }],
        }, {
            'model': UploadStatus,
            'enum': enums.UploadStatusEnum,
            'tables': [{
                'table': Upload,
                'field': 'status',
            }],
        }, {
            'model': UploadElementStatus,
            'enum': enums.UploadElementStatusEnum,
            'tables': [{
                'table': UploadElement,
                'field': 'status',
            }],
        }, {
            'model': PoolElementType,
            'enum': enums.PoolElementTypeEnum,
            'tables': [{
                'table': PoolElement,
                'field': 'type',
            }],
        }, {
            'model': SiteDataType,
            'enum': enums.SiteDataTypeEnum,
            'tables': [{
                'table': SiteData,
                'field': 'type',
            }],
        }, {
            'model': TagType,
            'enum': enums.TagTypeEnum,
            'tables': [{
                'table': Tag,
                'field': 'type',
            }],
        }, {
            'model': SiteDescriptor,
            'enum': enums.SiteDescriptorEnum,
            'tables': [{
                'table': ApiData,
                'field': 'site',
            }, {
                'table': Artist,
                'field': 'site',
            }, {
                'table': Illust,
                'field': 'site',
            }, {
                'table': IllustUrl,
                'field': 'site',
            }, {
                'table': IllustUrl,
                'field': 'sample_site',
            }],
        },
    ]


def reorganize_default_enums(config, model_enums):
    model = config['model']
    enum = config['enum']
    model_enums[enum.__name__] = template_dict = {}
    for key in model.__initial_mapping__:
        template_dict[key] = model.__initial_mapping__[key]
    for key in model.__mandatory_mapping__:
        template_dict[key] = model.__mandatory_mapping__[key]


# #### File functions

def get_migrations(is_local):
    subdir = 'local' if is_local else 'default'
    migration_directory = os.path.join(os.getcwd(), 'migrations', 'enum_versions', subdir)
    create_directory(migration_directory, isdir=True)
    migration_files = get_directory_listing(migration_directory)
    migrations = [put_get_json(os.path.join(migration_directory, file), 'r') for file in migration_files]
    ordered_migrations = []
    rev = None
    for _ in range(len(migrations)):
        next_migration = next((migration for migration in migrations if migration['down'] == rev))
        ordered_migrations.append(next_migration)
        rev = next_migration['rev']
    return ordered_migrations


def save_migration(migration, is_local):
    subdir = 'local' if is_local else 'default'
    migration_directory = os.path.join(os.getcwd(), 'migrations', 'enum_versions', subdir)
    filepath = os.path.join(migration_directory, migration['rev'] + '.json')
    put_get_json(filepath, 'w', migration)


# #### Database functions

def upgrade_tables(next_migration, prev_migration):
    for config in ENUMS_CONFIG:
        model = config['model']
        model_name = config['model']._model_name()
        if model_name not in next_migration['tables']:
            print("Skipping enum:", model_name)
        print("Converting enum:", model_name)
        next_values = next_migration['tables'][model_name]
        model.query.delete()
        for row in next_values:
            SESSION.add(model(**row))
        if prev_migration is None or model_name not in prev_migration['tables']:
            continue
        prev_values = prev_migration['tables'][model_name]
        mapping = {}
        unknown_val = None
        for next_item in next_values:
            prev_item = next((t for t in prev_values if t['name'] == next_item['name']), None)
            if prev_item is None:
                continue
            mapping[prev_item['id']] = next_item['id']
            if next_item['name'] == 'unknown':
                unknown_val = next_item['id']
        case_kw = {}
        if len(set(k['name'] for k in prev_values).difference(k['name'] for k in next_values)) > 0:
            case_kw['else_'] = unknown_val
        for table_info in config['tables']:
            table = table_info['table']
            field = table_info['field']
            field_attr = getattr(table, field)
            table.query.update({field: case(mapping, value=field_attr, **case_kw)})


def stamp_version(next_migration, current_revision):
    if current_revision is None:
        current_revision = Version(id='enum_version')
        SESSION.add(current_revision)
    current_revision.ver_num = next_migration['rev']


# #### Main execution functions

def generate_revision(args):
    new_migration = {}
    default_migrations = get_migrations(args.local)
    last_default = default_migrations[-1] if len(default_migrations) else None
    new_migration['branch'] = None
    new_migration['down'] = last_default['rev'] if last_default is not None else None
    new_migration['rev'] = uuid.uuid4().hex[-12:]
    new_migration['tables'] = tables = {}
    for config in ENUMS_CONFIG:
        enum = config['enum']
        table_name = config['model']._model_name()
        tables[table_name] = [{'id': k, 'name': v} for (k, v) in zip(enum.values, enum.names)]
    if last_default is not None and tables == last_default['tables']:
        print(f"Already at latest enum revision: {last_default['rev']}")
        return
    save_migration(new_migration, args.local)
    print(f"New migration generated: {new_migration['rev']}")


def upgrade_revision(args):
    migrations = get_migrations(args.local)
    if len(migrations) == 0:
        print("Must generate a migration first with the 'generate' command.")
        exit(-1)
    current_revision = Version.query.filter_by(id='enum_version').first()
    version_number = current_revision.ver_num if current_revision is not None else None
    next_migration = next((migration for migration in migrations if migration['down'] == version_number), None)
    if next_migration is None:
        print(f"Already at the latest version: {version_number}")
        return
    prev_migration = next((migration for migration in migrations if migration['rev'] == version_number), None)
    SESSION.execute(text("PRAGMA foreign_keys = 0"))
    try:
        upgrade_tables(next_migration, prev_migration)
        errors = SESSION.execute("PRAGMA foreign_key_check").fetchall()
        if len(errors) > 0:
            for (i, error) in enumerate(errors):
                print(f"Error record #{i + 1}:", *error)
            raise Exception(f"Upgrading to revision {next_migration['rev']} caused foreign key violations.")
        stamp_version(next_migration, current_revision)
    except Exception as e:
        print("Exception:", e)
        SESSION.rollback()
    else:
        SESSION.commit()
    SESSION.execute(text("PRAGMA foreign_keys = 1"))
    SESSION.remove()


def render_enums_file(args):
    enums_type = 'local' if args.local else 'default'
    model_enums = {}
    for config in ENUMS_CONFIG:
        if args.local:
            pass
        else:
            reorganize_default_enums(config, model_enums)
    template = Template(filename=os.path.join(os.getcwd(), 'migrations', 'enums.py.mako'))
    template_output = template.render_unicode(enums_type=enums_type, model_enums=model_enums)
    template_output = template_output.replace('\r\n', '\n').strip('\n') + '\n'
    enums_filepath = os.path.join(os.getcwd(), 'app', f'{enums_type}_enums.py')
    print(f"Writing {enums_type} enums module.")
    put_get_raw(enums_filepath, 'w', template_output)


def main(args):
    initialize(args)
    if args.action == 'generate':
        generate_revision(args)
    elif args.action == 'upgrade':
        upgrade_revision(args)
    elif args.action == 'render':
        render_enums_file(args)


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to load/modify enum and dependant tables.")
    parser.add_argument('action', choices=['generate', 'upgrade', 'render'], help="Choose which action to perform.")
    parser.add_argument('--local', required=False, action="store_true", default=False)
    args = parser.parse_args()

    main(args)
