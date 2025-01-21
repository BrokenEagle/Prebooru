# MIGRATIONS/VERSIONS/30474B49A614_DROP_CURRENT_SITE_ACCOUNT_FROM_ARTIST.PY
"""Drop current_site_account from artist

Revision ID: 30474b49a614
Revises: 942c4623c4de
Create Date: 2025-01-20 13:01:20.059915

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.columns import add_column, drop_column


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '30474b49a614'
down_revision = '942c4623c4de'
branch_labels = None
depends_on = None

ARTIST_CURRENT_SITE_ACCOUNT_DOWNGRADE = """
REPLACE INTO artist(id, site_id, site_artist_id, current_site_account, active, site_created, created, updated, "primary", profile_id, site_account_id, name_id)
SELECT artist.id, artist.site_id, artist.site_artist_id, label.name AS current_site_account, artist.active, artist.site_created, artist.created, artist.updated, artist."primary", artist.profile_id, artist.site_account_id, artist.name_id
FROM artist
JOIN label ON label.id = artist.site_account_id
"""

# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    drop_column('artist', 'current_site_account')


def downgrade_():
    connection = op.get_bind()

    print("Adding current_site_account column")
    add_column('artist', 'current_site_account', 'TEXT')

    print("Populating current_site_account column")
    connection.execute(ARTIST_CURRENT_SITE_ACCOUNT_DOWNGRADE)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

