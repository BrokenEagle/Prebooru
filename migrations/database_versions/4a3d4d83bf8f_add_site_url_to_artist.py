# MIGRATIONS/VERSIONS/4A3D4D83BF8F_ADD_SITE_URL_TO_ARTIST.PY
"""Add site_url to artist

Revision ID: 4a3d4d83bf8f
Revises: 8526a0931166
Create Date: 2025-09-08 10:34:30.772737

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column
from migrations.indexes import create_index, drop_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '4a3d4d83bf8f'
down_revision = '8526a0931166'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    add_column('artist', 'site_url', 'TEXT')
    create_index('artist', 'ix_artist_site_url', ['site_url'], True, sqlite_where='site_url IS NOT NULL')


def downgrade_():
    drop_index('artist', 'ix_artist_site_url')
    drop_column('artist', 'site_url')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

