# MIGRATIONS/VERSIONS/D6F086EA127C_ADD_UGOIRA_TABLE.PY
"""Add ugoira table

Revision ID: d6f086ea127c
Revises: 6b4945aa32b4
Create Date: 2025-08-24 13:40:04.402152

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import create_table, drop_table


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'd6f086ea127c'
down_revision = '6b4945aa32b4'
branch_labels = None
depends_on = None

UGOIRA_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'frames',
            'type': 'JSON',
            'nullable': False,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_ugoira',
            'columns': ['id'],
        },
    ],
    'with_rowid': True,
}


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    create_table('ugoira', **UGOIRA_TABLE_CONFIG)


def downgrade_():
    drop_table('ugoira')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

