# MIGRATIONS/VERSIONS/E35D8399BDCF_ADD_INDEX_TO_BOORU_ARTISTS_BOORU_ID.PY
"""Add index to booru artists booru ID

Revision ID: e35d8399bdcf
Revises: 02855d70f016
Create Date: 2024-11-29 17:45:54.187922

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.indexes import create_index, drop_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'e35d8399bdcf'
down_revision = '02855d70f016'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    create_index('booru_artists', 'ix_booru_artists_booru_id', ['booru_id'], False)


def downgrade_():
    drop_index('booru_artists', 'ix_booru_artists_booru_id', ['booru_id'], False)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
