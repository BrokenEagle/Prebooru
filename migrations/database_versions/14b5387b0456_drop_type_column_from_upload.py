"""Drop type column from Upload

Revision ID: 14b5387b0456
Revises: 7716d5a9071a
Create Date: 2022-09-29 12:02:53.104358

"""

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column, initialize_column, alter_column


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '14b5387b0456'
down_revision = '7716d5a9071a'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    print("Dropping type column")
    drop_column('upload', 'type')


def downgrade_():
    #print("Adding type column")
    #add_column('upload', 'type', 'String')

    print("Populating type column")
    extra_columns = [('request_url', 'String'), ('illust_url_id', 'Integer'), ('media_filepath', 'String')]
    for (_id, value, update, data) in initialize_column('upload', 'type', 'String', *extra_columns):
        if data['request_url'] is not None:
            type_name = 'post'
        elif data['illust_url_id'] is not None and data['media_filepath'] is not None:
            type_name = 'file'
        else:
            type_name = 'unknown'
        update(**{'type': type_name})

    print("Setting type column to non-nullable")
    alter_column('upload', 'type', 'VARCHAR', {'nullable': False})
