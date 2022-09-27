# MIGRATIONS/VERSIONS/7AFCB396FBD8_CHANGE_ARCHIVE_TYPE_TO_ENUM.PY
"""Change Archive type to enum

Revision ID: 7afcb396fbd8
Revises: d9bc63c007fa
Create Date: 2022-09-27 11:39:38.282545

"""

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column, alter_column, transfer_column
from migrations.indexes import create_index, drop_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '7afcb396fbd8'
down_revision = 'd9bc63c007fa'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def init():
    global ArchiveType
    from app.models.archive import ArchiveType


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    print("Initializing")
    init()

    print("Adding temp column")
    add_column('archive', 'temp', 'Integer')


    for (_id, value, update) in transfer_column('archive', ('type', 'String'), ('temp', 'Integer')):
        enum_value = ArchiveType[value].value
        update(**{'temp': enum_value})

    print("Dropping type/key index")
    drop_index('archive', 'ix_archive_type_archive_key')

    print("Dropping type column")
    drop_column('archive', 'type')

    print("Renaming temp column to type")
    alter_column('archive', 'temp', 'INTEGER', {'new_column_name': 'type', 'nullable': False})

    print("Adding type/key index")
    create_index('archive', 'ix_archive_type_archive_key', ['type', 'key'], True)


def downgrade_():
    print("Initializing")
    init()

    print("Adding temp column")
    add_column('archive', 'temp', 'String')

    print("Populating temp column")
    for (_id, value, update) in transfer_column('archive', ('type', 'Integer'), ('temp', 'String')):
        enum_name = ArchiveType(value).name
        update(**{'temp': enum_name})

    print("Dropping type/key index")
    drop_index('archive', 'ix_archive_type_archive_key')

    print("Dropping type column")
    drop_column('archive', 'type')

    print("Renaming temp column to type")
    alter_column('archive', 'temp', 'VARCHAR', {'new_column_name': 'type', 'nullable': False})

    print("Adding type/key index")
    create_index('archive', 'ix_archive_type_archive_key', ['type', 'key'], True)
