# MIGRATIONS/VERSIONS/BA9D1752C724_MODIFY_SIMILARITY_DATA_TABLE.PY
"""Modify similarity data table

Revision ID: ba9d1752c724
Revises: a5b752cf949b
Create Date: 2022-10-05 12:04:51.101306

"""
# ## PYTHON IMPORTS
import json

# ## PACKAGE IMPORTS
from migrations.tables import rename_table, remove_temp_tables
from migrations.columns import change_columns_type


# GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'ba9d1752c724'
down_revision = 'a5b752cf949b'
branch_labels = None
depends_on = None

DOWNGRADE_CONFIG = {
    'pk_similarity_data': {
        'type': 'primary',
        'args': (['id'],),
    },
    'fk_similarity_data_post_id_post': {
        'type': 'foreignkey',
        'args': ('post', ['post_id'], ['id'])
    },
}

UPGRADE_CONFIG = {
    'pk_image_hash': {
        'type': 'primary',
        'args': (['id'],),
    },
    'fk_image_hash_post_id_post': {
        'type': 'foreignkey',
        'args': ('post', ['post_id'], ['id'])
    },
}

UPGRADE_COLUMNS_CONFIG = {
    'chunk%02d' % i: {
        'from': 'String',
        'to': 'BLOB',
        'base': 'BLOB',
        'nullable': False,
    }
    for i in range(0, 32)
}

DOWNGRADE_COLUMNS_CONFIG = {
    'chunk%02d' % i: {
        'from': 'BLOB',
        'to': 'String',
        'base': 'VARCHAR',
        'nullable': False,
    }
    for i in range(0, 32)
}


# FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['similarity_data', 'image_hash'])

    rename_table('similarity_data', 'image_hash', DOWNGRADE_CONFIG, UPGRADE_CONFIG)

    for (mapped_data, update) in change_columns_type('image_hash', UPGRADE_COLUMNS_CONFIG):
        update_values = {}
        for col in UPGRADE_COLUMNS_CONFIG:
            update_values[col + '_temp'] = bytes.fromhex(mapped_data[col])
        update(**update_values)


def downgrade_():
    remove_temp_tables(['similarity_data', 'image_hash'])

    rename_table('image_hash', 'similarity_data', UPGRADE_CONFIG, DOWNGRADE_CONFIG)

    for (mapped_data, update) in change_columns_type('similarity_data', DOWNGRADE_COLUMNS_CONFIG):
        update_values = {}
        for col in DOWNGRADE_COLUMNS_CONFIG:
            update_values[col + '_temp'] = mapped_data[col].hex()
        update(**update_values)
