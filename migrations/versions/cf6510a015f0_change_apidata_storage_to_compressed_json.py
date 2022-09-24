# MIGRATIONS/VERSIONS/CF610A015F0_CHANGE_APIDATA_STORAGE_TO_COMPRESSED_JSON.PY
"""Change ApiData storage to compressed JSON

Revision ID: cf6510a015f0
Revises: cee25e958cb0
Create Date: 2022-09-23 05:40:07.242683

"""

# ## PYTHON IMPORTS
import json
import zlib

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column, alter_column, transfer_column


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'cf6510a015f0'
down_revision = 'cee25e958cb0'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    print("Adding temp column")
    add_column('api_data', 'temp', 'BLOB')

    print("Populating temp column")
    for (_id, value, update) in transfer_column('api_data', ('data', 'JSON'), ('temp', 'BLOB')):
        string_value = json.dumps(value, ensure_ascii=False, separators=(',', ':'))
        encoded_value = string_value.encode('UTF')
        update(**{'temp': zlib.compress(encoded_value)})

    print("Dropping data column")
    drop_column('api_data', 'data')

    print("Renaming temp column to data")
    alter_column('api_data', 'temp', 'BLOB', {'new_column_name': 'data', 'nullable': False})


def downgrade_():
    print("Adding temp column")
    add_column('api_data', 'temp', 'JSON')

    print("Populating temp column")
    for (_id, value, update) in transfer_column('api_data', ('data', 'BLOB'), ('temp', 'JSON')):
        decompressed_value = zlib.decompress(value)
        decoded_value = decompressed_value.decode('UTF')
        update(**{'temp': json.loads(decoded_value)})

    print("Dropping data column")
    drop_column('api_data', 'data')

    print("Renaming temp column to data")
    alter_column('api_data', 'temp', 'JSON', {'new_column_name': 'data', 'nullable': False})
