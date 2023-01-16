# MIGRATIONS/VERSIONS/5C54B3E09A84_UPDATE_CONSTRAINTS_FROM_ENUM_CHANGES.PY
"""Update constraints from enum changes

Revision ID: 5c54b3e09a84
Revises: 6b803ce90831
Create Date: 2022-11-28 22:03:24.387298

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations import batch_alter_table
from migrations.tables import remove_temp_tables
from migrations.constraints import create_constraints, drop_constraints, create_constraint, drop_constraint
from migrations.indexes import create_indexes, drop_indexes, create_index, drop_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '5c54b3e09a84'
down_revision = '6b803ce90831'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['archive', 'artist', 'illust'])

    drop_index('archive', 'ix_archive_type_key')
    create_constraint('archive', 'uq_archive_key_type_id', 'unique', (['key', 'type_id'],))

    # The previous migration already updated the columns from the previous migration, however, the name also needs to be changed
    with batch_alter_table('artist') as batch_op:
        drop_constraint(None, 'uq_artist_site_artist_id_site', 'unique', batch_op=batch_op)
        create_constraint(None, 'uq_artist_site_artist_id_site_id', 'unique', (['site_artist_id', 'site_id'],), batch_op=batch_op)

    # Same deal as with the artist table
    with op.batch_alter_table('illust', schema=None) as batch_op:
        drop_constraint(None, 'uq_illust_site_illust_id_site', 'unique', batch_op=batch_op)
        create_constraint(None, 'uq_illust_site_illust_id_site_id', 'unique', (['site_illust_id', 'site_id'],), batch_op=batch_op)


def downgrade_():
    remove_temp_tables(['archive', 'artist', 'illust'])

    with op.batch_alter_table('illust', schema=None) as batch_op:
        drop_constraint(None, 'uq_illust_site_illust_id_site_id', 'unique', batch_op=batch_op)
        create_constraint(None, 'uq_illust_site_illust_id_site', 'unique', (['site_illust_id', 'site_id'],), batch_op=batch_op)

    with batch_alter_table('artist') as batch_op:
        drop_constraint(None, 'uq_artist_site_artist_id_site_id', 'unique', batch_op=batch_op)
        create_constraint(None, 'uq_artist_site_artist_id_site', 'unique', (['site_artist_id', 'site_id'],), batch_op=batch_op)

    drop_constraint('archive', 'uq_archive_key_type_id')
    create_index('archive', 'ix_archive_type_key', ['key', 'type_id'], True)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass
