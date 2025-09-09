# MIGRATIONS/VERSIONS/8C3E136756AA_UPDATE_SITE_ILLUST_ID_ATTRIBUTES_ON_ILLUST.PY
"""Update site_illust_id attributes on illust

Revision ID: 8c3e136756aa
Revises: ba55e19f5d49
Create Date: 2025-09-09 12:17:07.582920

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations import batch_alter_table
from migrations.columns import alter_column
from migrations.constraints import create_constraint, drop_constraint
from migrations.indexes import create_index, drop_index, make_index_wrapper


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '8c3e136756aa'
down_revision = 'ba55e19f5d49'
branch_labels = None
depends_on = None

RESTORE_INDEX = make_index_wrapper('illust', [
    ('ix_illust_site_url', ['site_url'], True, {'sqlite_where': 'site_url IS NOT NULL'}),
])


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


@RESTORE_INDEX
def upgrade_():
    with batch_alter_table('illust', naming=True) as batch_op:
        alter_column(None, 'site_illust_id', 'INTEGER', {'nullable': True}, batch_op=batch_op)
        drop_constraint(None, 'uq_illust_site_illust_id_site_id', 'unique', batch_op=batch_op)
        create_constraint(None, 'ck_illust_identifier', 'check', ["""("site_illust_id" IS NULL) OR ("site_url" IS NULL)"""], batch_op=batch_op)

    create_index('illust', 'ix_illust_site_illust_id_site_id', ['site_illust_id', 'site_id'], True, sqlite_where='site_illust_id IS NOT NULL')


@RESTORE_INDEX
def downgrade_():
    drop_index('illust', 'ix_illust_site_illust_id_site_id')
    # Check constraints have to be dropped without naming enabled (default)
    drop_constraint('illust', 'ck_illust_identifier', 'check')

    with batch_alter_table('illust', naming=True) as batch_op:
        alter_column(None, 'site_illust_id', 'INTEGER', {'nullable': False}, batch_op=batch_op)
        create_constraint(None, 'uq_illust_site_illust_id_site_id', 'unique', (['site_illust_id', 'site_id'],), batch_op=batch_op)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

