# MIGRATIONS/VERSIONS/0D1F76CD873B_ADD_NAME_ID_TO_BOORU.PY
"""Add name_id to booru

Revision ID: 0d1f76cd873b
Revises: 1dd2fb6e38c8
Create Date: 2025-01-23 14:50:59.913453

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
revision = '0d1f76cd873b'
down_revision = '1dd2fb6e38c8'
branch_labels = None
depends_on = None

BOORU_NAME_ID_UPGRADE = """
REPLACE INTO booru(id, danbooru_id, current_name, banned, deleted, created, updated, name_id)
SELECT booru.id, booru.danbooru_id, booru.current_name, booru.banned, booru.deleted, booru.created, booru.updated, label.id AS site_account_id
FROM booru
LEFT JOIN label ON label.name = booru.current_name
"""

RESTORE_INDEX = make_index_wrapper('booru', [
    ('ix_booru_danbooru_id', ['danbooru_id'], True, {'sqlite_where': 'danbooru_id IS NOT NULL'}),
])


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


@RESTORE_INDEX
def upgrade_():
    connection = op.get_bind()

    print("Adding name_id column")
    add_column('booru', 'name_id', 'INTEGER')

    print("Populating name_id column")
    connection.execute(BOORU_NAME_ID_UPGRADE)

    print("Setting name_id as non-nullable and creating foreign key")
    with batch_alter_table('booru') as batch_op:
        alter_column(None, 'name_id', 'INTEGER', {'nullable': False}, batch_op=batch_op)
        create_constraint(None, 'fk_booru_name_id_label', 'foreignkey', ('label', ['name_id'], ['id']), batch_op=batch_op)


@RESTORE_INDEX
def downgrade_():
    print("Dropping name_id column and constraint")
    with batch_alter_table('booru') as batch_op:
        drop_constraint(None, 'fk_booru_name_id_label', 'foreignkey', batch_op=batch_op)
        drop_column(None, 'name_id', batch_op=batch_op)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
