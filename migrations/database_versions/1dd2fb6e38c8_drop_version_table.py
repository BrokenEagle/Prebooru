# MIGRATIONS/VERSIONS/1DD2FB6E38C8_DROP_VERSION_TABLE.PY
"""Drop version table

Revision ID: 1dd2fb6e38c8
Revises: 1cd3f9a22ff2
Create Date: 2025-01-23 00:35:45.529483

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import create_table, drop_table


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '1dd2fb6e38c8'
down_revision = '1cd3f9a22ff2'
branch_labels = None
depends_on = None

VERSION_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'id',
            'type': 'TEXT',
            'nullable': False,
        }, {
            'name': 'ver_num',
            'type': 'TEXT',
            'nullable': False,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_version',
            'columns': ['id'],
        },
    ],
    'with_rowid': False,
}

# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    drop_table('version')


def downgrade_():
    create_table('version', **VERSION_TABLE_CONFIG)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

