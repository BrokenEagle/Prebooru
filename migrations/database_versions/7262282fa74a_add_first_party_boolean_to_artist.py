# MIGRATIONS/VERSIONS/7262282FA74A_ADD_REPOSTER_BOOLEAN_TO_ARTIST.PY
"""Add primary boolean to artist

Revision ID: 7262282fa74a
Revises: 313468b3eacc
Create Date: 2023-02-03 21:09:07.041782

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column, alter_column, set_column_default


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '7262282fa74a'
down_revision = '313468b3eacc'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    add_column('artist', 'primary', 'BOOLEAN')
    set_column_default('artist', primary=1)
    alter_column('artist', 'primary', 'BOOLEAN', {'nullable': False})


def downgrade_():
    drop_column('artist', 'primary')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
