# MIGRATIONS/VERSIONS/D28849CEF17D_UPDATE_MANY_COLUMNS_TO_NONNULLABLE.PY
"""Update many columns to nonnullable

Revision ID: d28849cef17d
Revises: cf6510a015f0
Create Date: 2022-09-24 11:39:53.580896

"""

# ## PACKAGE IMPORTS
from migrations.columns import alter_column, alter_columns


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'd28849cef17d'
down_revision = 'cf6510a015f0'
branch_labels = None
depends_on = None


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    alter_columns('artist', [('active', 'BOOLEAN', {'nullable': False}),
                             ('current_site_account', 'VARCHAR', {'nullable': False}),
                             ('site_artist_id', 'INTEGER', {'nullable': False})])
    alter_columns('illust', [('active', 'BOOLEAN', {'nullable': False}),
                             ('pages', 'INTEGER', {'nullable': False}),
                             ('score', 'INTEGER', {'nullable': False})])
    alter_columns('illust_url', [('height', 'INTEGER', {'nullable': False}),
                                 ('width', 'INTEGER', {'nullable': False})])
    alter_columns('pool', [('created', 'DATETIME', {'nullable': False}),
                           ('updated', 'DATETIME', {'nullable': False})])
    alter_column('pool_element', 'type', 'VARCHAR', {'nullable': False})
    alter_column('similarity_data', 'ratio', 'FLOAT', {'nullable': False})
    alter_column('site_data', 'type', 'VARCHAR', {'nullable': False})
    alter_column('tag', 'type', 'VARCHAR', {'nullable': False})


def downgrade_():
    alter_columns('artist', [('active', 'BOOLEAN', {'nullable': True}),
                             ('current_site_account', 'VARCHAR', {'nullable': True}),
                             ('site_artist_id', 'INTEGER', {'nullable': True})])
    alter_columns('illust', [('active', 'BOOLEAN', {'nullable': True}),
                             ('pages', 'INTEGER', {'nullable': True}),
                             ('score', 'INTEGER', {'nullable': True})])
    alter_columns('illust_url', [('height', 'INTEGER', {'nullable': True}),
                                 ('width', 'INTEGER', {'nullable': True})])
    alter_columns('pool', [('created', 'DATETIME', {'nullable': True}),
                           ('updated', 'DATETIME', {'nullable': True})])
    alter_column('pool_element', 'type', 'VARCHAR', {'nullable': True})
    alter_column('similarity_data', 'ratio', 'FLOAT', {'nullable': True})
    alter_column('site_data', 'type', 'VARCHAR', {'nullable': True})
    alter_column('tag', 'type', 'VARCHAR', {'nullable': True})
