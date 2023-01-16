# MIGRATIONS/VERSIONS/E717AB741F9D_RENAME_SITE_ID_TO_SITE.PY
"""Rename site_id to site

Revision ID: e717ab741f9d
Revises: b16bf67f4760
Create Date: 2022-11-04 06:52:00.080588

"""

# ## PACKAGE IMPORTS
from migrations.tables import remove_temp_tables
from migrations.columns import alter_column, alter_columns


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'e717ab741f9d'
down_revision = 'b16bf67f4760'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['api_data', 'artist', 'illust', 'illust_url'])
    alter_column('api_data', 'site_id', 'INTEGER', {'new_column_name': 'site'})
    alter_column('artist', 'site_id', 'INTEGER', {'new_column_name': 'site'})
    alter_column('illust', 'site_id', 'INTEGER', {'new_column_name': 'site'})
    alter_columns('illust_url', [('site_id', 'INTEGER', {'new_column_name': 'site'}),
                                 ('sample_id', 'INTEGER', {'new_column_name': 'sample_site'}),
                                 ('sample', 'VARCHAR', {'new_column_name': 'sample_url'})])


def downgrade_():
    remove_temp_tables(['api_data', 'artist', 'illust', 'illust_url'])
    alter_column('api_data', 'site', 'INTEGER', {'new_column_name': 'site_id'})
    alter_column('artist', 'site', 'INTEGER', {'new_column_name': 'site_id'})
    alter_column('illust', 'site', 'INTEGER', {'new_column_name': 'site_id'})
    alter_columns('illust_url', [('site', 'INTEGER', {'new_column_name': 'site_id'}),
                                 ('sample_site', 'INTEGER', {'new_column_name': 'sample_id'}),
                                 ('sample_url', 'VARCHAR', {'new_column_name': 'sample'})])


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

