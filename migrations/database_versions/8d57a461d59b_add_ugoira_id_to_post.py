# MIGRATIONS/VERSIONS/8D57A461D59B_ADD_UGOIRA_ID_TO_POST.PY
"""Add ugoira_id to post

Revision ID: 8d57a461d59b
Revises: f2c919aab63a
Create Date: 2025-08-24 13:54:11.908395

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations import batch_alter_table
from migrations.columns import add_column, drop_column, alter_column
from migrations.constraints import create_constraint, drop_constraint


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '8d57a461d59b'
down_revision = 'f2c919aab63a'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    print("Adding ugoira_id column")
    add_column('post', 'ugoira_id', 'INTEGER')

    print("Creating foreign key")
    create_constraint('post', 'fk_post_ugoira_id_ugoira', 'foreignkey', ('ugoira', ['ugoira_id'], ['id']))


def downgrade_():
    print("Dropping ugoira column and constraint")
    with batch_alter_table('ugoira') as batch_op:
        drop_constraint(None, 'fk_post_ugoira_id_ugoira', 'foreignkey', batch_op=batch_op)
        drop_column(None, 'ugoira', batch_op=batch_op)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

