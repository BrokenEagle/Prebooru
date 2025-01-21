# MIGRATIONS/VERSIONS/F2B87DFA7F83_ADD_PROFILE_ID_TO_ARTIST_TABLE.PY
"""Add profile_id to artist table

Revision ID: f2b87dfa7f83
Revises: a40b61e1ecb5
Create Date: 2025-01-20 12:20:52.949383

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
revision = 'f2b87dfa7f83'
down_revision = 'a40b61e1ecb5'
branch_labels = None
depends_on = None

ARTIST_PROFILE_ID_UPGRADE = """
REPLACE INTO artist(id, site_id, site_artist_id, current_site_account, active, site_created, created, updated, "primary", profile_id)
SELECT artist.id, artist.site_id, artist.site_artist_id, artist.current_site_account, artist.active, artist.site_created, artist.created, artist.updated, artist."primary", artist_profile.description_id AS profile_id
FROM artist
JOIN (
    SELECT artist_profiles.artist_id, artist_profiles.description_id, ROW_NUMBER() OVER (PARTITION BY artist_profiles.artist_id ORDER BY artist_profiles.description_id DESC) AS rn
    FROM artist_profiles
) AS artist_profile ON artist_profile.artist_id = artist.id
WHERE artist_profile.rn = 1
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    connection = op.get_bind()

    print("Adding profile_id column")
    add_column('artist', 'profile_id', 'INTEGER')

    print("Populating profile_id column")
    connection.execute(ARTIST_PROFILE_ID_UPGRADE)

    print("Creating foreign key constraint")
    create_constraint('artist', 'fk_artist_profile_id_description', 'foreignkey', ('description', ['profile_id'], ['id']))


def downgrade_():
    print("Dropping profile_id column and constraint")
    with batch_alter_table('artist') as batch_op:
        drop_constraint(None, 'fk_artist_profile_id_description', 'foreignkey', batch_op=batch_op)
        drop_column(None, 'profile_id', batch_op=batch_op)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

