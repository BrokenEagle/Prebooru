# MIGRATIONS/VERSIONS/D9BC63C007FA_CHANGE_APIDATA_TYPE_TO_ENUM.PY
"""Change ApiData type to enum

Revision ID: d9bc63c007fa
Revises: d28849cef17d
Create Date: 2022-09-27 09:29:36.945297

"""

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column, alter_column, transfer_column


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'd9bc63c007fa'
down_revision = 'd28849cef17d'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def init():
    global ApiDataType
    from app.models.api_data import ApiDataType


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    print("Initializing")
    init()

    print("Adding temp column")
    add_column('api_data', 'temp', 'Integer')

    print("Populating temp column")
    for (_id, value, update) in transfer_column('api_data', ('type', 'String'), ('temp', 'Integer')):
        enum_value = ApiDataType[value].value
        update(**{'temp': enum_value})

    print("Dropping type column")
    drop_column('api_data', 'type')

    print("Renaming temp column to type")
    alter_column('api_data', 'temp', 'INTEGER', {'new_column_name': 'type', 'nullable': False})


def downgrade_():
    print("Initializing")
    init()

    print("Adding temp column")
    add_column('api_data', 'temp', 'String')

    print("Populating temp column")
    for (_id, value, update) in transfer_column('api_data', ('type', 'Integer'), ('temp', 'String')):
        enum_name = ApiDataType(value).name
        update(**{'temp': enum_name})

    print("Dropping type column")
    drop_column('api_data', 'type')

    print("Renaming temp column to type")
    alter_column('api_data', 'temp', 'VARCHAR', {'new_column_name': 'type', 'nullable': False})
