# MIGRATIONS/VERSIONS/C302A45B78FC_ADD_SITE_ACCOUNT_ID_COLUMN_TO_ARTIST.PY
"""Add site_account_id column to artist

Revision ID: c302a45b78fc
Revises: f2b87dfa7f83
Create Date: 2025-01-20 12:36:20.958111

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
revision = 'c302a45b78fc'
down_revision = 'f2b87dfa7f83'
branch_labels = None
depends_on = None

ARTIST_SITE_ACCOUNT_ID_UPGRADE = """
REPLACE INTO artist(id, site_id, site_artist_id, current_site_account, active, site_created, created, updated, "primary", profile_id, site_account_id)
SELECT artist.id, artist.site_id, artist.site_artist_id, artist.current_site_account, artist.active, artist.site_created, artist.created, artist.updated, artist."primary", artist.profile_id, label.id AS site_account_id
FROM artist
LEFT JOIN label ON label.name = artist.current_site_account
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    connection = op.get_bind()

    print("Adding site_account_id column")
    add_column('artist', 'site_account_id', 'INTEGER')

    print("Populating site_account_id column")
    connection.execute(ARTIST_SITE_ACCOUNT_ID_UPGRADE)

    print("Setting site_account_id as non-nullable and creating foreign key")
    with batch_alter_table('artist') as batch_op:
        alter_column(None, 'site_account_id', 'INTEGER', {'nullable': False}, batch_op=batch_op)
        create_constraint(None, 'fk_artist_site_account_id_label', 'foreignkey', ('label', ['site_account_id'], ['id']), batch_op=batch_op)


def downgrade_():
    print("Dropping site_account_id column and constraint")
    with batch_alter_table('artist') as batch_op:
        drop_constraint(None, 'fk_artist_site_account_id_label', 'foreignkey', batch_op=batch_op)
        drop_column(None, 'site_account_id', batch_op=batch_op)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

