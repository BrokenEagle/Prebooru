# MIGRATIONS/VERSIONS/B5E978344741_ADD_FRAMES_TO_ARCHIVE_POST.PY
"""Add frames to archive_post

Revision ID: b5e978344741
Revises: 8d57a461d59b
Create Date: 2025-08-24 15:00:31.508075

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'b5e978344741'
down_revision = '8d57a461d59b'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    add_column('archive_post', 'frames', 'JSON')


def downgrade_():
    drop_column('archive_post', 'frames', 'JSON')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

