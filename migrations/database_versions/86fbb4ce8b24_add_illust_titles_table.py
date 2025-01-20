# MIGRATIONS/VERSIONS/86FBB4CE8B24_ADD_ILLUST_TITLES_TABLE.PY
"""Add illust_titles table

Revision ID: 86fbb4ce8b24
Revises: 6461f170eb3b
Create Date: 2025-01-19 08:40:57.331934

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import create_table, drop_table


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '86fbb4ce8b24'
down_revision = '6461f170eb3b'
branch_labels = None
depends_on = None

OLD_TITLES_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'illust_id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'description_id',
            'type': 'INTEGER',
            'nullable': False,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_illust_titles',
            'columns': ['illust_id', 'description_id'],
        },
    ],
    'fk_config': [
        {
            'name': 'fk_illust_titles_illust_id_illust',
            'columns': ['illust_id'],
            'references': ['illust.id'],
        }, {
            'name': 'fk_illust_titles_description_id_description',
            'columns': ['description_id'],
            'references': ['description.id'],
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
    create_table('illust_titles', **OLD_TITLES_TABLE_CONFIG)


def downgrade_():
    drop_table('illust_titles')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

