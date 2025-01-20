# MIGRATIONS/VERSIONS/A40B61E1ECB5_DROP_SITE_DATA_TABLES.PY
"""Drop site data tables

Revision ID: a40b61e1ecb5
Revises: 9fddfae59105
Create Date: 2025-01-22 20:20:19.697199

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import create_table, drop_table
from migrations.indexes import create_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'a40b61e1ecb5'
down_revision = '9fddfae59105'
branch_labels = None
depends_on = None

SITE_DATA_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'illust_id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'title',
            'type': 'TEXT',
            'nullable': True,
        }, {
            'name': 'bookmarks',
            'type': 'INTEGER',
            'nullable': True,
        }, {
            'name': 'views',
            'type': 'INTEGER',
            'nullable': True,
        }, {
            'name': 'replies',
            'type': 'INTEGER',
            'nullable': True,
        }, {
            'name': 'retweets',
            'type': 'INTEGER',
            'nullable': True,
        }, {
            'name': 'quotes',
            'type': 'INTEGER',
            'nullable': True,
        }, {
            'name': 'type_id',
            'type': 'INTEGER',
            'nullable': True,
        }, {
            'name': 'site_uploaded',
            'type': 'INTEGER',
            'nullable': True,
        }, {
            'name': 'site_updated',
            'type': 'INTEGER',
            'nullable': True,
        }, {
            'name': 'redirector',
            'type': 'BOOLEAN',
            'nullable': False,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_site_data',
            'columns': ['id'],
        },
    ],
    'fk_config': [
        {
            'name': 'fk_site_data_illust_id_illust',
            'columns': ['illust_id'],
            'references': ['illust.id'],
        },
        {
            'name': 'fk_site_data_type_id_site_data_type',
            'columns': ['type_id'],
            'references': ['site_data_type.id'],
        },
    ],
    'with_rowid': True,
}

SITE_DATA_TYPE_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'name',
            'type': 'TEXT',
            'nullable': False,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_site_data_type',
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
    drop_table('site_data')
    drop_table('site_data_type')


def downgrade_():
    create_table('site_data_type', **SITE_DATA_TYPE_TABLE_CONFIG)
    create_table('site_data', **SITE_DATA_TABLE_CONFIG)
    create_index('site_data', 'ix_site_data_illust_id', ['illust_id'], False)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

