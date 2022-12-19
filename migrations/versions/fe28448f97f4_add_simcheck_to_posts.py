# MIGRATIONS/VERSIONS/FE28448F97F4_ADD_SIMCHECK_TO_POSTS.PY
"""Add simcheck to posts

Revision ID: fe28448f97f4
Revises: 144959993518
Create Date: 2022-12-16 16:58:07.004449

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import remove_temp_tables
from migrations.columns import add_column, drop_column, alter_column, set_column_default


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'fe28448f97f4'
down_revision = '144959993518'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['post'])
    add_column('post', 'simcheck', 'BOOLEAN')
    set_column_default('post', simcheck=0)
    alter_column('post', 'simcheck', 'BOOLEAN', {'nullable': False})


def downgrade_():
    drop_column('post', 'simcheck')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
