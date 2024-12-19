# MIGRATIONS/VERSIONS/20EF223031AD_REMOVE_DOMAIN_TABLE.PY
"""Remove domain table

Revision ID: 20ef223031ad
Revises: d9982f1c44b5
Create Date: 2024-12-18 16:56:04.855981

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import create_table, drop_table


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '20ef223031ad'
down_revision = 'd9982f1c44b5'
branch_labels = None
depends_on = None

DOMAIN_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'name',
            'type': 'TEXT',
            'nullable': False,
        }, {
            'name': 'redirector',
            'type': 'BOOLEAN',
            'nullable': False,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_domain',
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
    drop_table('domain')


def downgrade_():
    create_table('domain', **DOMAIN_TABLE_CONFIG)


def upgrade_jobs():
   pass


def downgrade_jobs():
    pass
