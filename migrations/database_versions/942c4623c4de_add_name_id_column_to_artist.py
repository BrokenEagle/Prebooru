# MIGRATIONS/VERSIONS/942C4623C4DE_ADD_NAME_ID_COLUMN_TO_ARTIST.PY
"""Add name_id column to artist

Revision ID: 942c4623c4de
Revises: c302a45b78fc
Create Date: 2025-01-20 12:51:13.116432

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations import batch_alter_table
from migrations.columns import add_column, drop_column
from migrations.constraints import create_constraint, drop_constraint


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '942c4623c4de'
down_revision = 'c302a45b78fc'
branch_labels = None
depends_on = None

ARTIST_NAME_ID_UPGRADE = """
REPLACE INTO artist(id, site_id, site_artist_id, current_site_account, active, site_created, created, updated, "primary", profile_id, site_account_id, name_id)
SELECT artist.id, artist.site_id, artist.site_artist_id, artist.current_site_account, artist.active, artist.site_created, artist.created, artist.updated, artist."primary", artist.profile_id, artist.site_account_id, artist_name.label_id AS name_id
FROM artist
JOIN (
    SELECT artist_names.artist_id, artist_names.label_id, ROW_NUMBER() OVER (PARTITION BY artist_names.artist_id ORDER BY artist_names.label_id DESC) AS rn
    FROM artist_names
) AS artist_name ON artist_name.artist_id = artist.id
WHERE artist_name.rn = 1
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    connection = op.get_bind()

    print("Adding name_id column")
    add_column('artist', 'name_id', 'INTEGER')

    print("Populating name_id column")
    connection.execute(ARTIST_NAME_ID_UPGRADE)

    print("Creating foreign key constraint")
    create_constraint('artist', 'fk_artist_name_id_label', 'foreignkey', ('label', ['name_id'], ['id']))


def downgrade_():
    print("Dropping name_id column and constraint")
    with batch_alter_table('artist') as batch_op:
        drop_constraint(None, 'fk_artist_name_id_label', 'foreignkey', batch_op=batch_op)
        drop_column(None, 'name_id', batch_op=batch_op)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

