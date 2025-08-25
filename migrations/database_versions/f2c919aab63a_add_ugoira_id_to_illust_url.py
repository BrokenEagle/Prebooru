# MIGRATIONS/VERSIONS/F2C919AAB63A_ADD_UGOIRA_ID_TO_ILLUST_URL.PY
"""Add ugoira_id to illust_url

Revision ID: f2c919aab63a
Revises: d6f086ea127c
Create Date: 2025-08-24 13:54:03.494585

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations import batch_alter_table
from migrations.columns import add_column, drop_column, alter_column
from migrations.constraints import create_constraint, drop_constraint
from migrations.indexes import make_index_wrapper


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'f2c919aab63a'
down_revision = 'd6f086ea127c'
branch_labels = None
depends_on = None

RESTORE_INDEX = make_index_wrapper('illust_url', [
    ('ix_illust_url_md5', ['md5'], False, {'sqlite_where': 'md5 IS NOT NULL'}),
])


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


@RESTORE_INDEX
def upgrade_():
    print("Adding ugoira_id column")
    add_column('illust_url', 'ugoira_id', 'INTEGER')

    print("Creating foreign key")
    create_constraint('illust_url', 'fk_illust_url_ugoira_id_ugoira', 'foreignkey', ('ugoira', ['ugoira_id'], ['id']))


@RESTORE_INDEX
def downgrade_():
    print("Dropping ugoira column and constraint")
    with batch_alter_table('ugoira') as batch_op:
        drop_constraint(None, 'fk_illust_url_ugoira_id_ugoira', 'foreignkey', batch_op=batch_op)
        drop_column(None, 'ugoira', batch_op=batch_op)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

