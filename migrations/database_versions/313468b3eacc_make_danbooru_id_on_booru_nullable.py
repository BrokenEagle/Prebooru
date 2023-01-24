# MIGRATIONS/VERSIONS/313468B3EACC_MAKE_DANBOORU_ID_ON_BOORU_NULLABLE.PY
"""Make Danbooru ID on booru nullable

Revision ID: 313468b3eacc
Revises: 5d148349fdbf
Create Date: 2023-01-21 18:58:50.455048

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.columns import alter_column
from migrations.constraints import create_constraint, drop_constraint
from migrations.indexes import create_index, drop_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '313468b3eacc'
down_revision = '5d148349fdbf'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    with op.batch_alter_table('booru', schema=None) as batch_op:
        alter_column(None, 'danbooru_id', 'INTEGER', {'nullable': True}, batch_op=batch_op)
        drop_constraint(None, 'uq_booru_danbooru_id', 'unique', batch_op=batch_op)

    create_index('booru', 'ix_booru_danbooru_id', ['danbooru_id'], unique=True, sqlite_where=sa.text('danbooru_id IS NOT NULL'))


def downgrade_():
    drop_index('booru', 'ix_booru_danbooru_id')

    with op.batch_alter_table('booru', schema=None) as batch_op:
        alter_column(None, 'danbooru_id', 'INTEGER', {'nullable': False}, batch_op=batch_op)
        create_constraint(None, 'uq_booru_danbooru_id', 'unique', (['danbooru_id'],), batch_op=batch_op)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
