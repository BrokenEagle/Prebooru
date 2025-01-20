# MIGRATIONS/VERSIONS/6461F170EB3B_ADD_COMMENTARY_ID_TO_ILLUST.PY
"""Add commentary_id to illust

Revision ID: 6461f170eb3b
Revises: e8216a78749f
Create Date: 2025-01-18 19:44:16.037327

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column
from migrations.constraints import create_constraint, drop_constraint


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '6461f170eb3b'
down_revision = 'e8216a78749f'
branch_labels = None
depends_on = None

ILLUST_COMMENTARY_ID_UPGRADE = """
REPLACE INTO illust(id, site_id, site_illust_id, artist_id, pages, score, active, site_created, created, updated, title_id, commentary_id)
SELECT illust.id, illust.site_id, illust.site_illust_id, illust.artist_id, illust.pages, illust.score, illust.active, illust.site_created, illust.created, illust.updated, illust.title_id, illust_comment.description_id AS commentary_id
FROM illust
JOIN (
    SELECT illust_commentaries.illust_id, illust_commentaries.description_id, ROW_NUMBER() OVER (PARTITION BY illust_commentaries.illust_id ORDER BY illust_commentaries.description_id ASC) AS rn
    FROM illust_commentaries
) AS illust_comment ON illust_comment.illust_id = illust.id
WHERE illust_comment.rn = 1
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    connection = op.get_bind()

    print("Adding commentary_id column")
    add_column('illust', 'commentary_id', 'INTEGER')

    print("Updating commentary_id column")
    connection.execute(ILLUST_COMMENTARY_ID_UPGRADE)

    print("Creating foreign key constraint")
    create_constraint('illust', 'fk_illust_commentary_id_description', 'foreignkey', ('description', ['commentary_id'], ['id']))

def downgrade_():
    drop_constraint('illust', 'fk_illust_commentary_id_description', 'foreignkey')
    drop_column('illust', 'commentary_id')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

