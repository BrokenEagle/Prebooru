# MIGRATIONS/VERSIONS/9FDDFAE59105_ADD_ADDITIONAL_COMMENTARIES_TABLE.PY
"""Add additional_commentaries table

Revision ID: 9fddfae59105
Revises: 4c4b06db9e14
Create Date: 2025-01-19 08:57:50.144478

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import create_table, drop_table


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '9fddfae59105'
down_revision = '4c4b06db9e14'
branch_labels = None
depends_on = None

ADDITIONAL_COMMENTARIES_TABLE_CONFIG = {
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
            'name': 'pk_additional_commentaries',
            'columns': ['illust_id', 'description_id'],
        },
    ],
    'fk_config': [
        {
            'name': 'fk_additional_commentaries_illust_id_illust',
            'columns': ['illust_id'],
            'references': ['illust.id'],
        }, {
            'name': 'fk_additional_commentaries_description_id_description',
            'columns': ['description_id'],
            'references': ['description.id'],
        },
    ],
    'with_rowid': False,
}

ADDITIONAL_COMMENTARIES_TABLE_INSERT = """
INSERT INTO additional_commentaries(illust_id, description_id)
SELECT illust_commentaries.illust_id, illust_commentaries.description_id
FROM illust_commentaries
"""

# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    connection = op.get_bind()

    print("Creating additional_commentaries table")
    create_table('additional_commentaries', **ADDITIONAL_COMMENTARIES_TABLE_CONFIG)

    print("Populating additional_commentaries table")
    connection.execute(ADDITIONAL_COMMENTARIES_TABLE_INSERT)


def downgrade_():
    drop_table('additional_commentaries')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

