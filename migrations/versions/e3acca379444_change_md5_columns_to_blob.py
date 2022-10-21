# MIGRATIONS/VERSIONS/E3ACCA379444_CHANGE_MD5_COLUMNS_TO_BLOB.PY
"""Change MD5 columns to blob

Revision ID: e3acca379444
Revises: c93c2735dc1c
Create Date: 2022-10-19 20:46:27.351983

"""

# ## PACKAGE IMPORTS
from migrations.tables import remove_temp_tables
from migrations.columns import change_columns_type
from migrations.indexes import create_index, drop_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'e3acca379444'
down_revision = 'c93c2735dc1c'
branch_labels = None
depends_on = None

UPGRADE_POST_COLUMNS_CONFIG = {
    'md5': {
        'from': 'String',
        'to': 'BLOB',
        'base': 'BLOB',
        'nullable': False,
    },
    'pixel_md5': {
        'from': 'String',
        'to': 'BLOB',
        'base': 'BLOB',
        'nullable': True,
    },
}

DOWNGRADE_POST_COLUMNS_CONFIG = {
    'md5': {
        'from': 'BLOB',
        'to': 'String',
        'base': 'VARCHAR',
        'nullable': False,
    },
    'pixel_md5': {
        'from': 'BLOB',
        'to': 'String',
        'base': 'VARCHAR',
        'nullable': True,
    },
}

UPGRADE_MEDIA_FILE_COLUMNS_CONFIG = {
    'md5': {
        'from': 'String',
        'to': 'BLOB',
        'base': 'BLOB',
        'nullable': False,
    },
}

DOWNGRADE_MEDIA_FILE_COLUMNS_CONFIG = {
    'md5': {
        'from': 'BLOB',
        'to': 'String',
        'base': 'VARCHAR',
        'nullable': False,
    },
}

UPGRADE_ELEMENT_COLUMNS_CONFIG = {
    'md5': {
        'from': 'String',
        'to': 'BLOB',
        'base': 'BLOB',
        'nullable': True,
    },
}

DOWNGRADE_ELEMENT_COLUMNS_CONFIG = {
    'md5': {
        'from': 'BLOB',
        'to': 'String',
        'base': 'VARCHAR',
        'nullable': True,
    },
}

# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['post', 'media_file', 'subscription_element', 'upload_element'])

    print("\nConverting post table")
    drop_index('post', 'ix_post_md5')
    for (mapped_data, update) in change_columns_type('post', UPGRADE_POST_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_POST_COLUMNS_CONFIG:
            update_values[col + '_temp'] = bytes.fromhex(mapped_data[col]) if mapped_data[col] is not None else None
        update(**update_values)
    create_index('post', 'ix_post_md5', ['md5'], True)

    print("\nConverting media_file table")
    for (mapped_data, update) in change_columns_type('media_file', UPGRADE_MEDIA_FILE_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_MEDIA_FILE_COLUMNS_CONFIG:
            update_values[col + '_temp'] = bytes.fromhex(mapped_data[col])
        update(**update_values)

    print("\nConverting subscription_element table")
    drop_index('subscription_element', 'ix_subscription_element_md5')
    for (mapped_data, update) in change_columns_type('subscription_element', UPGRADE_ELEMENT_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_ELEMENT_COLUMNS_CONFIG:
            update_values[col + '_temp'] = bytes.fromhex(mapped_data[col]) if mapped_data[col] is not None else None
        update(**update_values)
    create_index('subscription_element', 'ix_subscription_element_md5', ['md5'], False, sqlite_where='md5 IS NOT NULL')

    print("\nConverting upload_element table")
    drop_index('upload_element', 'ix_upload_element_md5')
    for (mapped_data, update) in change_columns_type('upload_element', UPGRADE_ELEMENT_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_ELEMENT_COLUMNS_CONFIG:
            update_values[col + '_temp'] = bytes.fromhex(mapped_data[col]) if mapped_data[col] is not None else None
        update(**update_values)
    create_index('upload_element', 'ix_upload_element_md5', ['md5'], False, sqlite_where='md5 IS NOT NULL')


def downgrade_():
    remove_temp_tables(['post', 'media_file', 'subscription_element', 'upload_element'])

    print("\nConverting post table")
    drop_index('post', 'ix_post_md5')
    for (mapped_data, update) in change_columns_type('post', DOWNGRADE_POST_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_POST_COLUMNS_CONFIG:
            update_values[col + '_temp'] = mapped_data[col].hex() if mapped_data[col] is not None else None
        update(**update_values)
    create_index('post', 'ix_post_md5', ['md5'], True)

    print("\nConverting media_file table")
    for (mapped_data, update) in change_columns_type('media_file', DOWNGRADE_MEDIA_FILE_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_MEDIA_FILE_COLUMNS_CONFIG:
            update_values[col + '_temp'] = mapped_data[col].hex()
        update(**update_values)

    print("\nConverting subscription_element table")
    drop_index('subscription_element', 'ix_subscription_element_md5')
    for (mapped_data, update) in change_columns_type('subscription_element', DOWNGRADE_ELEMENT_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_ELEMENT_COLUMNS_CONFIG:
            update_values[col + '_temp'] = mapped_data[col].hex() if mapped_data[col] is not None else None
        update(**update_values)
    create_index('subscription_element', 'ix_subscription_element_md5', ['md5'], False, sqlite_where='md5 IS NOT NULL')

    print("\nConverting upload_element table")
    drop_index('upload_element', 'ix_upload_element_md5')
    for (mapped_data, update) in change_columns_type('upload_element', DOWNGRADE_ELEMENT_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_ELEMENT_COLUMNS_CONFIG:
            update_values[col + '_temp'] = mapped_data[col].hex() if mapped_data[col] is not None else None
        update(**update_values)
    create_index('upload_element', 'ix_upload_element_md5', ['md5'], False, sqlite_where='md5 IS NOT NULL')
