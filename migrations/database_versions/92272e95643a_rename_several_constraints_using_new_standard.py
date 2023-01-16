# MIGRATIONS/VERSIONS/92272E95643A_RENAME_SEVERAL_CONSTRAINTS_USING_NEW_STANDARD.PY
"""Rename several constraints using new standard

Revision ID: 92272e95643a
Revises: 5ef65fe1b761
Create Date: 2022-10-16 21:39:23.682963

"""
# ## PACKAGE IMPORTS
from migrations.tables import remove_temp_tables
from migrations.indexes import create_index, drop_index
from migrations.constraints import create_constraint, drop_constraint


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '92272e95643a'
down_revision = '5ef65fe1b761'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['archive', 'artist', 'illust'])
    drop_index('archive', 'ix_archive_type_archive_key')
    create_index('archive', 'ix_archive_type_key', ['type', 'key'], True)
    drop_constraint('artist', 'uq_artist_site_id', 'unique')
    create_constraint('artist', 'uq_artist_site_id_site_artist_id', 'unique', ['site_id', 'site_artist_id'])
    drop_constraint('illust', 'uq_illust_site_id', 'unique')
    create_constraint('illust', 'uq_illust_site_id_site_illust_id', 'unique', ['site_id', 'site_illust_id'])


def downgrade_():
    remove_temp_tables(['archive', 'artist', 'illust'])
    drop_index('archive', 'ix_archive_type_key')
    create_index('archive', 'ix_archive_type_archive_key', ['type', 'key'], True)
    drop_constraint('artist', 'uq_artist_site_id_site_artist_id', 'unique')
    create_constraint('artist', 'uq_artist_site_id', 'unique', ['site_id', 'site_artist_id'])
    drop_constraint('illust', 'uq_illust_site_id_site_illust_id', 'unique')
    create_constraint('illust', 'uq_illust_site_id', 'unique', ['site_id', 'site_illust_id'])
