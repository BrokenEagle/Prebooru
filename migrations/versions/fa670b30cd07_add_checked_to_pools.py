# MIGRATIONS/VERSIONS/FA670B30CD07_ADD_CHECKED_TO_POOLS.PY
"""Add checked to pools

Revision ID: fa670b30cd07
Revises: b16bf67f4760
Create Date: 2022-12-01 15:57:02.821947

"""

# ## PACKAGE IMPORTS
from migrations.tables import remove_temp_tables
from migrations.columns import add_column, drop_column


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'fa670b30cd07'
down_revision = '5c54b3e09a84'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['pool'])
    add_column('pool', 'checked', 'INTEGER')


def downgrade_():
    remove_temp_tables(['pool'])
    drop_column('pool', 'checked')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

