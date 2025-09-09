# MIGRATIONS/VERSIONS/0AB8339C117E_UPDATE_SITE_ARTIST_ID_ATTRIBUTES_ON_ARTIST.PY
"""Update site_artist_id attributes on artist

Revision ID: 0ab8339c117e
Revises: 4a3d4d83bf8f
Create Date: 2025-09-08 10:40:10.825243

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations import batch_alter_table
from migrations.columns import alter_column
from migrations.constraints import create_constraint, drop_constraint
from migrations.indexes import create_index, drop_index, make_index_wrapper


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '0ab8339c117e'
down_revision = '4a3d4d83bf8f'
branch_labels = None
depends_on = None


RESTORE_INDEX = make_index_wrapper('artist', [
    ('ix_artist_site_url', ['site_url'], True, {'sqlite_where': 'site_url IS NOT NULL'}),
])

# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


@RESTORE_INDEX
def upgrade_():
    with batch_alter_table('artist', naming=True) as batch_op:
        alter_column(None, 'site_artist_id', 'INTEGER', {'nullable': True}, batch_op=batch_op)
        drop_constraint(None, 'uq_artist_site_artist_id_site_id', 'unique', batch_op=batch_op)
        create_constraint(None, 'ck_artist_identifier', 'check', ["""("site_artist_id" IS NULL) OR ("site_url" IS NULL)"""], batch_op=batch_op)

    create_index('artist', 'ix_artist_site_artist_id_site_id', ['site_artist_id', 'site_id'], True, sqlite_where='site_artist_id IS NOT NULL')


@RESTORE_INDEX
def downgrade_():
    drop_index('artist', 'ix_artist_site_artist_id_site_id')
    # Check constraints have to be dropped without naming enabled (default)
    drop_constraint('artist', 'ck_artist_identifier', 'check')

    with batch_alter_table('artist', naming=True) as batch_op:
        alter_column(None, 'site_artist_id', 'INTEGER', {'nullable': False}, batch_op=batch_op)
        create_constraint(None, 'uq_artist_site_artist_id_site_id', 'unique', (['site_artist_id', 'site_id'],), batch_op=batch_op)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

