# MIGRATIONS/VERSIONS/1CD3F9A22FF2_PRUNE_ARTIST_M2M_TABLES.PY
"""Prune artist M2M tables

Revision ID: 1cd3f9a22ff2
Revises: 30474b49a614
Create Date: 2025-01-20 13:07:16.931954

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '1cd3f9a22ff2'
down_revision = '30474b49a614'
branch_labels = None
depends_on = None

ARTIST_PROFILES_TABLE_PRUNE = """
DELETE FROM artist_profiles
WHERE (artist_profiles.artist_id, artist_profiles.description_id) IN (
    SELECT artist.id, artist.profile_id
    FROM artist
    WHERE artist.profile_id IS NOT NULL
)
"""

ARTIST_SITE_ACCOUNTS_TABLE_PRUNE = """
DELETE FROM artist_site_accounts
WHERE (artist_site_accounts.artist_id, artist_site_accounts.label_id) IN (
    SELECT artist.id, artist.site_account_id
    FROM artist
)
"""

ARTIST_NAMES_TABLE_PRUNE = """
DELETE FROM artist_names
WHERE (artist_names.artist_id, artist_names.label_id) IN (
    SELECT artist.id, artist.name_id
    FROM artist
    WHERE artist.name_id IS NOT NULL
)
"""

ARTIST_PROFILES_TABLE_POPULATE = """
INSERT INTO artist_profiles(artist_id, description_id)
SELECT artist.id, artist.profile_id
FROM artist
WHERE artist.profile_id IS NOT NULL
"""

ARTIST_SITE_ACCOUNTS_TABLE_POPULATE = """
INSERT INTO artist_site_accounts(artist_id, description_id)
SELECT artist.id, artist.site_account_id
FROM artist
"""

ARTIST_NAMES_TABLE_POPULATE = """
INSERT INTO artist_names(artist_id, description_id)
SELECT artist.id, artist.name_id
FROM artist
WHERE artist.name_id IS NOT NULL
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    connection = op.get_bind()

    print("Pruning artist_profiles table")
    connection.execute(ARTIST_PROFILES_TABLE_PRUNE)

    print("Pruning artist_site_accounts table")
    connection.execute(ARTIST_SITE_ACCOUNTS_TABLE_PRUNE)

    print("Pruning artist_names table")
    connection.execute(ARTIST_NAMES_TABLE_PRUNE)


def downgrade_():
    connection = op.get_bind()

    print("Populating artist_profiles table")
    connection.execute(ARTIST_PROFILES_TABLE_POPULATE)

    print("Populating artist_site_accounts table")
    connection.execute(ARTIST_SITE_ACCOUNTS_TABLE_POPULATE)

    print("Populating artist_names table")
    connection.execute(ARTIST_NAMES_TABLE_POPULATE)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

