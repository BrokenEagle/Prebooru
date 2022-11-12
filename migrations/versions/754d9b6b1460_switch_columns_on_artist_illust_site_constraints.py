# MIGRATIONS/VERSIONS/754D9B6B1460_SWITCH_COLUMNS_ON_ARTIST_ILLUST_SITE_CONSTRAINTS.PY
"""Switch columns on artist/illust site constraints

Revision ID: 754d9b6b1460
Revises: e717ab741f9d
Create Date: 2022-11-12 15:20:23.849273

"""

# ## PACKAGE IMPORTS
from migrations.constraints import create_constraint, drop_constraint
from migrations.tables import remove_temp_tables


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '754d9b6b1460'
down_revision = 'e717ab741f9d'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    remove_temp_tables(['artist', 'illust'])

    print("Dropping constraints")
    drop_constraint('artist', 'uq_artist_site_id_site_artist_id', 'unique')
    drop_constraint('illust', 'uq_illust_site_id_site_illust_id', 'unique')

    print("Adding constraints")
    create_constraint('artist', 'uq_artist_site_artist_id_site', 'unique', ['site_artist_id', 'site'])
    create_constraint('illust', 'uq_illust_site_illust_id_site', 'unique', ['site_illust_id', 'site'])


def downgrade_():
    remove_temp_tables(['artist', 'illust'])

    print("Dropping constraints")
    drop_constraint('artist', 'uq_artist_site_artist_id_site', 'unique')
    drop_constraint('illust', 'uq_illust_site_illust_id_site', 'unique')

    print("Adding constraints")
    create_constraint('artist', 'uq_artist_site_id_site_artist_id', 'unique', ['site', 'site_artist_id'])
    create_constraint('illust', 'uq_illust_site_id_site_illust_id', 'unique', ['site', 'site_illust_id'])


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

