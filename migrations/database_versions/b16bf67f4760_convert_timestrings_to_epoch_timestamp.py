# MIGRATIONS/VERSIONS/B16BF67F4760_CONVERT_TIMESTRINGS_TO_EPOCH_TIMESTAMP.PY
"""Convert timestrings to epoch timestamp

Revision ID: b16bf67f4760
Revises: e3acca379444
Create Date: 2022-10-20 16:52:40.264964

"""

# ## PACKAGE IMPORTS
from migrations.tables import remove_temp_tables
from migrations.columns import change_columns_type
from migrations.indexes import create_indexes, drop_indexes
from utility.time import datetime_to_epoch, datetime_from_epoch

# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'b16bf67f4760'
down_revision = 'e3acca379444'
branch_labels = None
depends_on = None

UPGRADE_CREATED_COLUMNS_CONFIG = {
    'created': {
        'from': 'DATETIME',
        'to': 'INTEGER',
        'base': 'INTEGER',
        'nullable': False,
    },
}

DOWNGRADE_CREATED_COLUMNS_CONFIG = {
    'created': {
        'from': 'INTEGER',
        'to': 'DATETIME',
        'base': 'VARCHAR',
        'nullable': False,
    },
}

UPGRADE_EXPIRES_COLUMNS_CONFIG = {
    'expires': {
        'from': 'DATETIME',
        'to': 'INTEGER',
        'base': 'INTEGER',
        'nullable': False,
    },
}

DOWNGRADE_EXPIRES_COLUMNS_CONFIG = {
    'expires': {
        'from': 'INTEGER',
        'to': 'DATETIME',
        'base': 'VARCHAR',
        'nullable': False,
    },
}

UPGRADE_CREATED_UPDATED_COLUMNS_CONFIG = {
    'created': {
        'from': 'DATETIME',
        'to': 'INTEGER',
        'base': 'INTEGER',
        'nullable': False,
    },
    'updated': {
        'from': 'DATETIME',
        'to': 'INTEGER',
        'base': 'INTEGER',
        'nullable': False,
    },
}

DOWNGRADE_CREATED_UPDATED_COLUMNS_CONFIG = {
    'created': {
        'from': 'INTEGER',
        'to': 'DATETIME',
        'base': 'VARCHAR',
        'nullable': False,
    },
    'updated': {
        'from': 'INTEGER',
        'to': 'DATETIME',
        'base': 'VARCHAR',
        'nullable': False,
    },
}

UPGRADE_ILLUST_ARTIST_COLUMNS_CONFIG = {
    'site_created': {
        'from': 'DATETIME',
        'to': 'INTEGER',
        'base': 'INTEGER',
        'nullable': True,
    },
    'created': {
        'from': 'DATETIME',
        'to': 'INTEGER',
        'base': 'INTEGER',
        'nullable': False,
    },
    'updated': {
        'from': 'DATETIME',
        'to': 'INTEGER',
        'base': 'INTEGER',
        'nullable': False,
    },
}

DOWNGRADE_ILLUST_ARTIST_COLUMNS_CONFIG = {
    'site_created': {
        'from': 'INTEGER',
        'to': 'DATETIME',
        'base': 'VARCHAR',
        'nullable': True,
    },
    'created': {
        'from': 'INTEGER',
        'to': 'DATETIME',
        'base': 'VARCHAR',
        'nullable': False,
    },
    'updated': {
        'from': 'INTEGER',
        'to': 'DATETIME',
        'base': 'VARCHAR',
        'nullable': False,
    },
}

UPGRADE_SITE_DATA_COLUMNS_CONFIG = {
    'site_uploaded': {
        'from': 'DATETIME',
        'to': 'INTEGER',
        'base': 'INTEGER',
        'nullable': True,
    },
    'site_updated': {
        'from': 'DATETIME',
        'to': 'INTEGER',
        'base': 'INTEGER',
        'nullable': True,
    },
}

DOWNGRADE_SITE_DATA_COLUMNS_CONFIG = {
    'site_uploaded': {
        'from': 'INTEGER',
        'to': 'DATETIME',
        'base': 'VARCHAR',
        'nullable': True,
    },
    'site_updated': {
        'from': 'INTEGER',
        'to': 'DATETIME',
        'base': 'VARCHAR',
        'nullable': True,
    },
}

UPGRADE_SUBSCRIPTION_COLUMNS_CONFIG = {
    'requery': {
        'from': 'DATETIME',
        'to': 'INTEGER',
        'base': 'INTEGER',
        'nullable': True,
    },
    'checked': {
        'from': 'DATETIME',
        'to': 'INTEGER',
        'base': 'INTEGER',
        'nullable': True,
    },
    'created': {
        'from': 'DATETIME',
        'to': 'INTEGER',
        'base': 'INTEGER',
        'nullable': False,
    },
    'updated': {
        'from': 'DATETIME',
        'to': 'INTEGER',
        'base': 'INTEGER',
        'nullable': False,
    },
}

DOWNGRADE_SUBSCRIPTION_COLUMNS_CONFIG = {
    'requery': {
        'from': 'INTEGER',
        'to': 'DATETIME',
        'base': 'VARCHAR',
        'nullable': True,
    },
    'checked': {
        'from': 'INTEGER',
        'to': 'DATETIME',
        'base': 'VARCHAR',
        'nullable': True,
    },
    'created': {
        'from': 'INTEGER',
        'to': 'DATETIME',
        'base': 'VARCHAR',
        'nullable': False,
    },
    'updated': {
        'from': 'INTEGER',
        'to': 'DATETIME',
        'base': 'VARCHAR',
        'nullable': False,
    },
}


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['post', 'upload', 'error', 'api_data', 'media_file', 'archive', 'subscription_element',
                        'booru', 'notation', 'pool', 'artist', 'illust', 'site_data', 'subscription'])

    # ## CREATED only

    print("\nConverting post table")
    for (mapped_data, update) in change_columns_type('post', UPGRADE_CREATED_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_CREATED_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_to_epoch(mapped_data[col])
        update(**update_values)

    print("\nConverting upload table")
    for (mapped_data, update) in change_columns_type('upload', UPGRADE_CREATED_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_CREATED_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_to_epoch(mapped_data[col])
        update(**update_values)

    print("\nConverting error table")
    for (mapped_data, update) in change_columns_type('error', UPGRADE_CREATED_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_CREATED_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_to_epoch(mapped_data[col])
        update(**update_values)

    # ## EXPIRES only

    print("\nConverting api_data table")
    for (mapped_data, update) in change_columns_type('api_data', UPGRADE_EXPIRES_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_EXPIRES_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_to_epoch(mapped_data[col])
        update(**update_values)

    print("\nConverting media_file table")
    for (mapped_data, update) in change_columns_type('media_file', UPGRADE_EXPIRES_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_EXPIRES_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_to_epoch(mapped_data[col])
        update(**update_values)

    UPGRADE_EXPIRES_COLUMNS_CONFIG['expires']['nullable'] = True

    print("\nConverting archive table")
    for (mapped_data, update) in change_columns_type('archive', UPGRADE_EXPIRES_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_EXPIRES_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_to_epoch(mapped_data[col]) if mapped_data[col] is not None else None
        update(**update_values)

    print("\nConverting subscription_element table")
    drop_indexes('subscription_element', ['ix_subscription_element_md5', 'ix_subscription_element_post_id'])
    for (mapped_data, update) in change_columns_type('subscription_element', UPGRADE_EXPIRES_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_EXPIRES_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_to_epoch(mapped_data[col]) if mapped_data[col] is not None else None
        update(**update_values)
    create_indexes('subscription_element',
        [
            ('ix_subscription_element_md5', ['md5'], False, {'sqlite_where': 'md5 IS NOT NULL'}),
            ('ix_subscription_element_post_id', ['post_id'], False, {'sqlite_where': 'post_id IS NOT NULL'}),
        ]
    )

    # ## CREATED/UPDATED only

    print("\nConverting booru table")
    for (mapped_data, update) in change_columns_type('booru', UPGRADE_CREATED_UPDATED_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_CREATED_UPDATED_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_to_epoch(mapped_data[col])
        update(**update_values)

    print("\nConverting notation table")
    for (mapped_data, update) in change_columns_type('notation', UPGRADE_CREATED_UPDATED_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_CREATED_UPDATED_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_to_epoch(mapped_data[col])
        update(**update_values)

    print("\nConverting pool table")
    for (mapped_data, update) in change_columns_type('pool', UPGRADE_CREATED_UPDATED_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_CREATED_UPDATED_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_to_epoch(mapped_data[col])
        update(**update_values)

    # ## ARTIST/ILLUST

    print("\nConverting artist table")
    for (mapped_data, update) in change_columns_type('artist', UPGRADE_ILLUST_ARTIST_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_ILLUST_ARTIST_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_to_epoch(mapped_data[col]) if mapped_data[col] is not None else None
        update(**update_values)

    print("\nConverting illust table")
    for (mapped_data, update) in change_columns_type('illust', UPGRADE_ILLUST_ARTIST_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_ILLUST_ARTIST_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_to_epoch(mapped_data[col]) if mapped_data[col] is not None else None
        update(**update_values)

    # ## SITE DATA

    print("\nConverting site_data table")
    for (mapped_data, update) in change_columns_type('site_data', UPGRADE_SITE_DATA_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_SITE_DATA_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_to_epoch(mapped_data[col]) if mapped_data[col] is not None else None
        update(**update_values)

    # ## SUBSCRIPTION

    print("\nConverting subscription table")
    for (mapped_data, update) in change_columns_type('subscription', UPGRADE_SUBSCRIPTION_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_SUBSCRIPTION_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_to_epoch(mapped_data[col]) if mapped_data[col] is not None else None
        update(**update_values)


def downgrade_():
    remove_temp_tables(['post', 'upload', 'error', 'api_data', 'media_file', 'archive', 'subscription_element',
                        'booru', 'notation', 'pool', 'artist', 'illust', 'site_data', 'subscription'])

    # ## CREATED only

    print("\nConverting post table")
    for (mapped_data, update) in change_columns_type('post', DOWNGRADE_CREATED_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_CREATED_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_from_epoch(mapped_data[col])
        update(**update_values)

    print("\nConverting upload table")
    for (mapped_data, update) in change_columns_type('upload', DOWNGRADE_CREATED_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_CREATED_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_from_epoch(mapped_data[col])
        update(**update_values)

    print("\nConverting error table")
    for (mapped_data, update) in change_columns_type('error', DOWNGRADE_CREATED_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_CREATED_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_from_epoch(mapped_data[col])
        update(**update_values)

    # ## EXPIRES only

    print("\nConverting api_data table")
    for (mapped_data, update) in change_columns_type('api_data', DOWNGRADE_EXPIRES_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_EXPIRES_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_from_epoch(mapped_data[col])
        update(**update_values)

    print("\nConverting media_file table")
    for (mapped_data, update) in change_columns_type('media_file', DOWNGRADE_EXPIRES_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_EXPIRES_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_from_epoch(mapped_data[col])
        update(**update_values)

    DOWNGRADE_EXPIRES_COLUMNS_CONFIG['expires']['nullable'] = True

    print("\nConverting archive table")
    for (mapped_data, update) in change_columns_type('archive', DOWNGRADE_EXPIRES_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_EXPIRES_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_from_epoch(mapped_data[col]) if mapped_data[col] is not None else None
        update(**update_values)

    print("\nConverting subscription_element table")
    drop_indexes('subscription_element', ['ix_subscription_element_md5', 'ix_subscription_element_post_id'])
    for (mapped_data, update) in change_columns_type('subscription_element', DOWNGRADE_EXPIRES_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_EXPIRES_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_from_epoch(mapped_data[col]) if mapped_data[col] is not None else None
        update(**update_values)
    create_indexes('subscription_element',
        [
            ('ix_subscription_element_md5', ['md5'], False, {'sqlite_where': 'md5 IS NOT NULL'}),
            ('ix_subscription_element_post_id', ['post_id'], False, {'sqlite_where': 'post_id IS NOT NULL'}),
        ]
    )

    # ## CREATED/UPDATED only

    print("\nConverting booru table")
    for (mapped_data, update) in change_columns_type('booru', DOWNGRADE_CREATED_UPDATED_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_CREATED_UPDATED_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_from_epoch(mapped_data[col])
        update(**update_values)

    print("\nConverting notation table")
    for (mapped_data, update) in change_columns_type('notation', DOWNGRADE_CREATED_UPDATED_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_CREATED_UPDATED_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_from_epoch(mapped_data[col])
        update(**update_values)

    print("\nConverting pool table")
    for (mapped_data, update) in change_columns_type('pool', DOWNGRADE_CREATED_UPDATED_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_CREATED_UPDATED_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_from_epoch(mapped_data[col])
        update(**update_values)

    # ## ARTIST/ILLUST

    print("\nConverting artist table")
    for (mapped_data, update) in change_columns_type('artist', DOWNGRADE_ILLUST_ARTIST_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_ILLUST_ARTIST_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_from_epoch(mapped_data[col]) if mapped_data[col] is not None else None
        update(**update_values)

    print("\nConverting illust table")
    for (mapped_data, update) in change_columns_type('illust', DOWNGRADE_ILLUST_ARTIST_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_ILLUST_ARTIST_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_from_epoch(mapped_data[col]) if mapped_data[col] is not None else None
        update(**update_values)

    # ## SITE DATA

    print("\nConverting site_data table")
    for (mapped_data, update) in change_columns_type('site_data', DOWNGRADE_SITE_DATA_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_SITE_DATA_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_from_epoch(mapped_data[col]) if mapped_data[col] is not None else None
        update(**update_values)

    # ## SUBSCRIPTION

    print("\nConverting subscription table")
    for (mapped_data, update) in change_columns_type('subscription', DOWNGRADE_SUBSCRIPTION_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_SUBSCRIPTION_COLUMNS_CONFIG:
            update_values[col + '_temp'] = datetime_from_epoch(mapped_data[col]) if mapped_data[col] is not None else None
        update(**update_values)
