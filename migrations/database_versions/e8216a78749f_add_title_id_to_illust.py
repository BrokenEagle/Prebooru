# MIGRATIONS/VERSIONS/E8216A78749F_ADD_TITLE_ID_TO_ILLUST.PY
"""Add title_id to illust

Revision ID: e8216a78749f
Revises: d2c16d9d9233
Create Date: 2025-01-18 18:45:55.739150

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column
from migrations.constraints import create_constraint, drop_constraint


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'e8216a78749f'
down_revision = 'd2c16d9d9233'
branch_labels = None
depends_on = None

DESCRIPTION_TITLE_INSERT = """
INSERT INTO description(body)
SELECT DISTINCT site_data.title
FROM site_data
WHERE site_data.title IS NOT NULL and site_data.title NOT IN (
    SELECT description.body
    FROM description
)
"""

ILLUST_TITLE_ID_UPGRADE = """
REPLACE INTO illust(id, site_id, site_illust_id, artist_id, pages, score, active, site_created, created, updated, title_id)
SELECT illust.id, illust.site_id, illust.site_illust_id, illust.artist_id, illust.pages, illust.score, illust.active, illust.site_created, illust.created, illust.updated, description.id AS title_id
FROM illust
JOIN site_data ON site_data.illust_id = illust.id
JOIN description ON description.body = site_data.title
WHERE site_data.title IS NOT NULL
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    connection = op.get_bind()

    print("Updating description table")
    connection.execute(DESCRIPTION_TITLE_INSERT)

    print("Adding title_id column")
    add_column('illust', 'title_id', 'INTEGER')

    print("Updating title_id column")
    connection.execute(ILLUST_TITLE_ID_UPGRADE)

    print("Creating foreign key constraint")
    create_constraint('illust', 'fk_illust_title_id_description', 'foreignkey', ('description', ['title_id'], ['id']))


def downgrade_():
    drop_constraint('illust', 'fk_illust_title_id_description', 'foreignkey')
    drop_column('illust', 'title_id')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

