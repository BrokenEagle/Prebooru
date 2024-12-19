# MIGRATIONS/VERSIONS/D9982F1C44B5_REMOVE_SUCCESSES_FAILURES_FROM_UPLOADS.PY
"""Remove successes/failures from uploads

Revision ID: d9982f1c44b5
Revises: e35d8399bdcf
Create Date: 2024-12-18 15:52:36.618680

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import remove_temp_tables
from migrations.columns import add_columns, drop_columns, alter_columns, set_column_default


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'd9982f1c44b5'
down_revision = 'e35d8399bdcf'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['upload'])
    drop_columns('upload', ['successes', 'failures'])


def downgrade_():
    remove_temp_tables(['upload'])
    add_columns('upload', [('successes', 'INTEGER'), ('failures', 'INTEGER')])
    set_column_default('upload', successes=0, failures=0)
    alter_columns('upload', [('successes', 'INTEGER', {'nullable': False}),
                             ('failures', 'INTEGER', {'nullable': False})])


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
