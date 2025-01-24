# MIGRATIONS/VERSIONS/430C72C99D1F_DROP_CURRENT_NAME_FROM_BOORU.PY
"""Drop current_name from booru

Revision ID: 430c72c99d1f
Revises: 0d1f76cd873b
Create Date: 2025-01-23 15:23:31.326235

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column, alter_column
from migrations.indexes import make_index_wrapper

# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '430c72c99d1f'
down_revision = '0d1f76cd873b'
branch_labels = None
depends_on = None

BOORU_CURRENT_NAME_DOWNGRADE = """
REPLACE INTO booru(id, danbooru_id, current_name, banned, deleted, created, updated, name_id)
SELECT booru.id, booru.danbooru_id, label.name AS current_name, booru.banned, booru.deleted, booru.created, booru.updated, booru.name_id
FROM booru
JOIN label ON label.id = booru.name_id
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
    drop_column('booru', 'current_name')


@RESTORE_INDEX
def downgrade_():
    connection = op.get_bind()

    print("Adding current_name column")
    add_column('booru', 'current_name', 'TEXT')

    print("Populating current_name column")
    connection.execute(BOORU_CURRENT_NAME_DOWNGRADE)

    print("Setting name_id as non-nullable and creating foreign key")
    alter_column('booru', 'current_name', 'TEXT', {'nullable': False})


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

