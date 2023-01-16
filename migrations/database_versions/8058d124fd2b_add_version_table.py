# MIGRATIONS/VERSIONS/8058D124FD2B_ADD_VERSION_TABLE.PY
"""Add version table

Revision ID: 8058d124fd2b
Revises: f1e2a6875b1e
Create Date: 2022-11-23 11:43:00.810901

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
# Add migrations or other local imports here


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '8058d124fd2b'
down_revision = 'f1e2a6875b1e'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    op.create_table('version',
        sa.Column('id', sa.TEXT(), nullable=False),
        sa.Column('ver_num', sa.TEXT(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_version')),
        sqlite_with_rowid=False
    )


def downgrade_():
    op.drop_table('version')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

