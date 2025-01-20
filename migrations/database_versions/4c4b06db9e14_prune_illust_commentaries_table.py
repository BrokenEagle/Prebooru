# MIGRATIONS/VERSIONS/4C4B06DB9E14_PRUNE_ILLUST_COMMENTARIES_TABLE.PY
"""Prune illust_commentaries table

Revision ID: 4c4b06db9e14
Revises: 86fbb4ce8b24
Create Date: 2025-01-19 08:49:51.880900

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '4c4b06db9e14'
down_revision = '86fbb4ce8b24'
branch_labels = None
depends_on = None

ILLUST_COMMENTARIES_TABLE_PRUNE = """
DELETE FROM illust_commentaries
WHERE (illust_commentaries.illust_id, illust_commentaries.description_id) IN (
    SELECT illust.id, illust.commentary_id
    FROM illust
    WHERE illust.commentary_id IS NOT NULL
)
"""

ILLUST_COMMENTARIES_TABLE_POPULATE = """
INSERT INTO illust_commentaries(illust_id, description_id)
SELECT illust.id, illust.commentary_id
FROM illust
WHERE illust.commentary_id IS NOT NULL
"""

# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    connection = op.get_bind()
    connection.execute(ILLUST_COMMENTARIES_TABLE_PRUNE)


def downgrade_():
    connection = op.get_bind()
    connection.execute(ILLUST_COMMENTARIES_TABLE_POPULATE)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

