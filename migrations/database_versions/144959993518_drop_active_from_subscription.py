# MIGRATIONS/VERSIONS/144959993518_DROP_ACTIVE_FROM_SUBSCRIPTION.PY
"""Drop active from subscription

Revision ID: 144959993518
Revises: fa670b30cd07
Create Date: 2022-12-07 20:13:56.319646

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import remove_temp_tables
from migrations.columns import add_column, drop_column, initialize_column, alter_column


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '144959993518'
down_revision = 'fa670b30cd07'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['subscription'])
    drop_column('subscription', 'active')


def downgrade_():
    remove_temp_tables(['subscription'])
    add_column('subscription', 'active', 'BOOLEAN')
    connection = op.get_bind()
    connection.execute(sa.text('UPDATE subscription SET active=1'))
    alter_column('subscription', 'active', 'BOOLEAN', {'nullable': False})


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
