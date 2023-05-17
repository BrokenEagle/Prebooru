# MIGRATE_ENUMS.PY

# ## PYTHON IMPORTS
import os
import uuid
import functools
from argparse import ArgumentParser

# ## EXTERNAL IMPORTS
from sqlalchemy import text, func
from sqlalchemy.sql import case, label, union_all
from mako.template import Template

# ## PACKAGE IMPORTS
from utility.file import create_directory, get_directory_listing, put_get_json, put_get_raw
from app import SESSION


# ## FUNCTIONS

# #### Initialize functions

def initialize_imports(args):
    """Items that must be imported after environment variables are set."""
    global SESSION, Version, create_directory, get_directory_listing, put_get_json, put_get_raw
    from app import SESSION
    from app.models import Version
    from utility.file import create_directory, get_directory_listing, put_get_json, put_get_raw


def initialize_enums_config(args):
    global ENUMS_CONFIG
    from app.models.model_enums import SiteDescriptor, ApiDataType, ArchiveType, PostType, SubscriptionStatus,\
        SubscriptionElementStatus, SubscriptionElementKeep, UploadStatus, UploadElementStatus, PoolElementType,\
        SiteDataType, TagType, MediaAssetLocation
    from app.models import ApiData, Archive, Artist, Illust, IllustUrl, PoolElement, Post, SiteData,\
        Subscription, SubscriptionElement, Upload, UploadElement, Tag, MediaAsset
    if args.local:
        try:
            from app.logical.enums import local as enums
        except ImportError:
            from app.logical.enums import default as enums
    else:
        from app.logical.enums import default as enums
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
            'model': MediaAssetLocation,
            'enum': enums.MediaAssetLocationEnum,
            'tables': [{
                'table': MediaAsset,
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


# #### Auxiliary functions

def reorganize_default_enums(config, model_enums):
    """Organizes the enums by their current defaults in the enum model file."""
    model = config['model']
    enum = config['enum']
    model_enums[enum.__name__] = template_dict = {}
    for key in model.__initial_mapping__:
        template_dict[key] = model.__initial_mapping__[key]
    for key in model.__mandatory_mapping__:
        template_dict[key] = model.__mandatory_mapping__[key]


def sort_local_enums(config, model_enums):
    """Sorts the enums by prevalance, starting at 0 and incrementing by 1."""
    model = config['model']
    enum = config['enum']
    if len(config['tables']) > 1:
        reorder_local_enum_field_class_multiple(config, model_enums)
    else:
        reorder_local_enums_field_classes_single(config, model_enums)
    template_dict = model_enums[enum.__name__]
    for key in model.__initial_mapping__:
        if key not in template_dict:
            template_dict[key] = model.__initial_mapping__[key]
    for key in model.__mandatory_mapping__:
        template_dict[key] = model.__mandatory_mapping__[key]
    model_enums[enum.__name__] = dict(sorted(template_dict.items(), key=lambda x: x[1]))


def make_enum_dict(reorder_result):
    return {result[0].name: i for (i, result) in enumerate(reorder_result)}


def get_migration_by_rev(version_number, migrations):
    return next(filter(lambda x: x['rev'] == version_number, migrations), None)


def get_migration_by_down(version_number, migrations):
    return next(filter(lambda x: x['down'] == version_number, migrations), None)


def get_migrations_by_branch(version_number, migrations):
    return [migration for migration in migrations if migration['branch'] == version_number]


# #### File functions

@functools.lru_cache(maxsize=2)
def get_migration_data(subdir):
    migration_directory = os.path.join(os.getcwd(), 'migrations', 'enum_versions', subdir)
    create_directory(migration_directory, isdir=True)
    migration_files = get_directory_listing(migration_directory)
    return [put_get_json(os.path.join(migration_directory, file), 'r') for file in migration_files]


def get_branch_migrations(is_local, version_number):
    subdir = 'local' if is_local else 'default'
    migrations = get_migration_data(subdir)
    found_migration = next(filter(lambda x: x['rev'] == version_number, migrations), None)
    if found_migration is None:
        if not is_local:
            return []
        default_migrations = get_migration_data('default')
        default_head = next(filter(lambda x: x['rev'] == version_number, default_migrations), None)
        if default_head is None:
            return []
        branch_migrations = [migration for migration in migrations if migration['branch'] == version_number]
    else:
        branch_migrations = migrations
    ordered_migrations = []
    rev = None
    for _ in range(len(branch_migrations)):
        next_migration = next((migration for migration in migrations if migration['down'] == rev))
        ordered_migrations.append(next_migration)
        rev = next_migration['rev']
    return ordered_migrations


def is_default_revision(version_number):
    return any(migration for migration in get_migration_data('default') if migration['rev'] == version_number)


def save_migration(migration, is_local):
    subdir = 'local' if is_local else 'default'
    migration_directory = os.path.join(os.getcwd(), 'migrations', 'enum_versions', subdir)
    filepath = os.path.join(migration_directory, migration['rev'] + '.json')
    put_get_json(filepath, 'w', migration)


# #### Database functions

def apply_current_enums(config, model_enums):
    model = config['model']
    enum = config['enum']
    items = model.query.order_by(model.id.asc()).all()
    model_enums[enum.__name__] = {item.name: item.id for item in items}


def reorder_local_enums_field_classes_single(config, model_enums):
    enum = config['enum']
    table_info = config['tables'][0]
    table = table_info['table']
    field = table_info['field']
    field_attr = getattr(table, field)
    count_label = label('count_unique', func.count(field_attr))
    reorder_result = table.query.filter(field_attr.is_not(None)).group_by(field_attr).order_by(count_label.desc())\
                                .with_entities(field_attr, count_label).all()
    model_enums[enum.__name__] = make_enum_dict(reorder_result)


def reorder_local_enum_field_class_multiple(config, model_enums):
    model = config['model']
    enum = config['enum']
    unique_column = 'unique_' + model._model_name()
    unions = []
    for table_info in config['tables']:
        table = table_info['table']
        field = table_info['field']
        field_attr = getattr(table, field)
        label_attr = label(unique_column, field_attr)
        unions.append(table.query.filter(label_attr.is_not(None)).with_entities(label_attr))
    model_group = union_all(*unions).cte('model_group')
    unique_attr = getattr(model_group.columns, unique_column)
    unique_count = label('count_unique', func.count(unique_attr))
    reorder_result = SESSION.query(model_group).group_by(unique_attr).order_by(unique_count.desc())\
                                               .with_entities(unique_attr, unique_count).all()
    model_enums[enum.__name__] = make_enum_dict(reorder_result)


def migrate_tables(next_migration, prev_migration):
    for config in ENUMS_CONFIG:
        model = config['model']
        model_name = model._model_name()
        if model_name not in next_migration['tables']:
            print("Skipping enum:", model_name)
        next_values = next_migration['tables'][model_name]
        current_values = model.query.all()
        if len(next_values) == len(current_values):
            for current in current_values:
                nextval = next((v for v in next_values if v['id'] == current.id and v['name'] == current.name), None)
                if nextval is None:
                    print(current, next_values)
                    break
            else:
                print("Skipping enum:", model_name)
                continue
        print("Converting enum:", model_name)
        model.query.delete()
        for row in next_values:
            SESSION.add(model(**row))
        if prev_migration is None or model_name not in prev_migration['tables']:
            SESSION.flush()
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
            print(mapping, field_attr, case_kw)
            table.query.update({field: case(mapping, value=field_attr, **case_kw)})


def run_migration(to_migration, from_migration, revison_number):
    SESSION.execute(text("PRAGMA foreign_keys = 0"))
    try:
        migrate_tables(to_migration, from_migration)
        errors = SESSION.execute("PRAGMA foreign_key_check").fetchall()
        if len(errors) > 0:
            for (i, error) in enumerate(errors):
                print(f"Error record #{i + 1}:", *error)
            raise Exception(f"Upgrading to revision {to_migration['rev']} caused foreign key violations.")
        stamp_version(to_migration, revison_number)
    except Exception as e:
        print("Exception:", e)
        SESSION.rollback()
    else:
        SESSION.commit()
    SESSION.execute(text("PRAGMA foreign_keys = 1"))
    SESSION.remove()


def stamp_version(next_migration, current_revision):
    if current_revision is None:
        current_revision = Version(id='enum_version')
        SESSION.add(current_revision)
    current_revision.ver_num = next_migration['rev']


# #### Main execution functions

def generate_revision(args):
    current_revision = Version.query.filter_by(id='enum_version').first()
    version_number = current_revision.ver_num if current_revision is not None else None
    migrations = get_branch_migrations(args.local, version_number)
    last_migration = migrations[-1] if len(migrations) else None
    new_migration = {}
    if args.local:
        if last_migration is None:
            if not is_default_revision(version_number):
                print(f"Unable to find version {version_number} if default enums folder to branch off of.")
            new_migration['branch'] = version_number
        else:
            new_migration['branch'] = last_migration['branch']
    else:
        new_migration['branch'] = None
    new_migration['down'] = last_migration['rev'] if last_migration is not None else None
    new_migration['rev'] = uuid.uuid4().hex[-12:]
    new_migration['tables'] = tables = {}
    for config in ENUMS_CONFIG:
        enum = config['enum']
        table_name = config['model']._model_name()
        tables[table_name] = [{'id': k, 'name': v} for (k, v) in zip(enum.values, enum.names)]
    if last_migration is not None and tables == last_migration['tables']:
        print(f"Already at latest enum revision: {last_migration['rev']}")
        return
    save_migration(new_migration, args.local)
    print(f"New migration generated: {new_migration['rev']}")


def upgrade_revision(args):
    current_revision = Version.query.filter_by(id='enum_version').first()
    version_number = current_revision.ver_num if current_revision is not None else None
    migrations = get_branch_migrations(args.local, version_number)
    if len(migrations) == 0:
        if version_number is None:
            print("Must generate a migration first with the 'generate' command.")
        else:
            print(f"Unable to find migrations for revision {version_number}.")
        exit(-1)
    if args.local and migrations[0]['branch'] == version_number:
        next_migration = migrations[0]
    else:
        next_migration = get_migration_by_down(version_number, migrations)
        if next_migration is None:
            print(f"Already at the latest version: {version_number}")
            return
    if args.local and next_migration['down'] is None:
        current_migration = get_migration_by_rev(next_migration['branch'], get_migration_data('default'))
    else:
        current_migration = get_migration_by_rev(version_number, migrations)
    run_migration(next_migration, current_migration, current_revision)


def downgrade_revision(args):
    current_revision = Version.query.filter_by(id='enum_version').first()
    version_number = current_revision.ver_num if current_revision is not None else None
    if version_number is None:
        print("No upgrade migration has yet been run.")
        exit(-1)
    migrations = get_branch_migrations(args.local, version_number)
    if len(migrations) == 0:
        print(f"Unable to find migrations for revision {version_number}.")
        exit(-1)
    current_migration = get_migration_by_rev(version_number, migrations)
    if current_migration is None:
        print(f"Beginning of branch {version_number} has been reached.")
        exit(-1)
    if current_migration['down'] is None:
        if not args.local:
            print("Beginning of default branch has been reached.")
            exit(-1)
        previous_migration = get_migration_by_rev(current_migration['branch'], get_migration_data('default'))
    else:
        previous_migration = get_migration_by_rev(current_migration['down'], migrations)
    run_migration(previous_migration, current_migration, current_revision)


def render_enums_file(args):
    enums_type = 'local' if args.local else 'default'
    model_enums = {}
    for config in ENUMS_CONFIG:
        if args.actual:
            apply_current_enums(config, model_enums)
        elif args.local:
            sort_local_enums(config, model_enums)
        else:
            reorganize_default_enums(config, model_enums)
    template = Template(filename=os.path.join(os.getcwd(), 'migrations', 'enums.py.mako'))
    template_output = template.render_unicode(enums_type=enums_type, model_enums=model_enums)
    template_output = template_output.replace('\r\n', '\n').strip('\n') + '\n'
    enums_filepath = os.path.join(os.getcwd(), 'app', 'logical', 'enums', f'{enums_type}.py')
    print(f"Writing {enums_type} enums module.")
    put_get_raw(enums_filepath, 'w', template_output)


def main(args):
    os.environ['USE_ENUMS'] = 'true'
    initialize_imports(args)
    initialize_enums_config(args)
    if args.action == 'render':
        render_enums_file(args)
    elif args.action == 'generate':
        generate_revision(args)
    elif args.action == 'upgrade':
        upgrade_revision(args)
    elif args.action == 'downgrade':
        downgrade_revision(args)


# ##EXECUTION START

if __name__ == '__main__':
    parser = ArgumentParser(description="Fix script to load/modify enum and dependant tables.")
    parser.add_argument('action', choices=['render', 'generate', 'upgrade', 'downgrade'],
                        help="Choose which action to perform.")
    parser.add_argument('--local', required=False, action="store_true", default=False)
    parser.add_argument('--actual', required=False, action="store_true", default=False)
    args = parser.parse_args()

    main(args)
