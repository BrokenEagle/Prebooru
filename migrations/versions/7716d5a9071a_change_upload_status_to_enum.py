# MIGRATIONS/VERSIONS/7716D5A9071A_CHANGE_UPLOAD_STATUS_TO_ENUM.PY
"""Change Upload status to enum

Revision ID: 7716d5a9071a
Revises: 7771df7c354b
Create Date: 2022-09-29 11:46:03.951309

"""

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column, alter_column, transfer_column


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '7716d5a9071a'
down_revision = '7771df7c354b'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def init():
    global UploadStatus
    from app.models.upload import UploadStatus


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    print("Initializing")
    init()

    print("Adding temp column")
    add_column('upload', 'temp', 'Integer')

    print("Populating temp column")
    for (_id, value, update) in transfer_column('upload', ('status', 'String'), ('temp', 'Integer')):
        enum_value = UploadStatus[value].value
        update(**{'temp': enum_value})

    print("Dropping status column")
    drop_column('upload', 'status')

    print("Renaming temp column to status")
    alter_column('upload', 'temp', 'INTEGER', {'new_column_name': 'status', 'nullable': False})


def downgrade_():
    print("Initializing")
    init()

    print("Adding temp column")
    add_column('upload', 'temp', 'String')

    print("Populating temp column")
    for (_id, value, update) in transfer_column('upload', ('status', 'Integer'), ('temp', 'String')):
        enum_name = UploadStatus(value).name
        update(**{'temp': enum_name})

    print("Dropping status column")
    drop_column('upload', 'status')

    print("Renaming temp column to status")
    alter_column('upload', 'temp', 'VARCHAR', {'new_column_name': 'status', 'nullable': False})
