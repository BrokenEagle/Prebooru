# MIGRATIONS/VERSIONS/BA55E19F5D49_ADD_SITE_URL_TO_ILLUST.PY
"""Add site_url to illust

Revision ID: ba55e19f5d49
Revises: 0ab8339c117e
Create Date: 2025-09-09 12:11:26.062293

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column
from migrations.indexes import create_index, drop_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'ba55e19f5d49'
down_revision = '0ab8339c117e'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    add_column('illust', 'site_url', 'TEXT')
    create_index('illust', 'ix_illust_site_url', ['site_url'], True, sqlite_where='site_url IS NOT NULL')


def downgrade_():
    drop_index('artist', 'ix_artist_site_url')
    drop_column('artist', 'site_url')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

