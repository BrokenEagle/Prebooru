# MIGRATIONS/VERSIONS/563512FB9995_PRUNE_BOORU_NAMES_TABLE.PY
"""Prune booru_names table

Revision ID: 563512fb9995
Revises: 430c72c99d1f
Create Date: 2025-01-23 15:34:10.745877

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '563512fb9995'
down_revision = '430c72c99d1f'
branch_labels = None
depends_on = None

BOORU_NAMES_TABLE_PRUNE = """
DELETE FROM booru_names
WHERE (booru_names.booru_id, booru_names.label_id) IN (
    SELECT booru.id, booru.name_id
    FROM booru
    WHERE booru.name_id IS NOT NULL
)
"""

BOORU_NAMES_TABLE_POPULATE = """
INSERT INTO booru_names(booru_id, label_id)
SELECT booru.id, booru.name_id
FROM booru
WHERE booru.name_id IS NOT NULL
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    connection = op.get_bind()
    connection.execute(BOORU_NAMES_TABLE_PRUNE)


def downgrade_():
    connection = op.get_bind()
    connection.execute(BOORU_NAMES_TABLE_POPULATE)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

