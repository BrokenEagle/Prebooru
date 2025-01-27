# MIGRATIONS/VERSIONS/B5EC37C7A2F6_CHANGE_PRIMARY_KEY_ORDER_OF_BOORU_M2M_TABLES.PY
"""Change primary key order of booru M2M tables

Revision ID: b5ec37c7a2f6
Revises: 563512fb9995
Create Date: 2025-01-27 10:29:57.918752

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import create_table, drop_table
from migrations.indexes import create_index, drop_index


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'b5ec37c7a2f6'
down_revision = '563512fb9995'
branch_labels = None
depends_on = None

OLD_BOORU_ARTISTS_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'artist_id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'booru_id',
            'type': 'INTEGER',
            'nullable': False,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_booru_names',
            'columns': ['artist_id', 'booru_id'],
        },
    ],
    'fk_config': [
        {
            'name': 'pk_booru_names_artist_id_artist',
            'columns': ['artist_id'],
            'references': ['artist.id'],
        }, {
            'name': 'pk_booru_names_booru_id_booru',
            'columns': ['booru_id'],
            'references': ['booru.id'],
        },
    ],
    'with_rowid': False,
}

NEW_BOORU_ARTISTS_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'booru_id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'artist_id',
            'type': 'INTEGER',
            'nullable': False,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_booru_names',
            'columns': ['booru_id', 'artist_id'],
        },
    ],
    'fk_config': [
        {
            'name': 'pk_booru_names_booru_id_booru',
            'columns': ['booru_id'],
            'references': ['booru.id'],
        }, {
            'name': 'pk_booru_names_artist_id_artist',
            'columns': ['artist_id'],
            'references': ['artist.id'],
        },
    ],
    'with_rowid': False,
}

OLD_BOORU_NAMES_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'label_id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'booru_id',
            'type': 'INTEGER',
            'nullable': False,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_booru_names',
            'columns': ['label_id', 'booru_id'],
        },
    ],
    'fk_config': [
        {
            'name': 'pk_booru_names_label_id_label',
            'columns': ['label_id'],
            'references': ['label.id'],
        }, {
            'name': 'pk_booru_names_booru_id_booru',
            'columns': ['booru_id'],
            'references': ['booru.id'],
        },
    ],
    'with_rowid': False,
}

NEW_BOORU_NAMES_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'booru_id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'label_id',
            'type': 'INTEGER',
            'nullable': False,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_booru_names',
            'columns': ['booru_id', 'label_id'],
        },
    ],
    'fk_config': [
        {
            'name': 'pk_booru_names_booru_id_booru',
            'columns': ['booru_id'],
            'references': ['booru.id'],
        }, {
            'name': 'pk_booru_names_label_id_label',
            'columns': ['label_id'],
            'references': ['label.id'],
        },
    ],
    'with_rowid': False,
}

INSERT_BOORU_ARTISTS = """
INSERT INTO booru_artists_temp(booru_id, artist_id)
SELECT booru_artists.booru_id, booru_artists.artist_id
FROM booru_artists
"""

INSERT_BOORU_NAMES = """
INSERT INTO booru_names_temp(booru_id, label_id)
SELECT booru_names.booru_id, booru_names.label_id
FROM booru_names
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    connection = op.get_bind()

    print("Dropping index")
    drop_index('booru_artists', 'ix_booru_artists_booru_id')

    print("Migrating booru_artists table")
    create_table('booru_artists_temp', **NEW_BOORU_ARTISTS_TABLE_CONFIG)
    connection.execute(INSERT_BOORU_ARTISTS)
    drop_table('booru_artists')
    op.rename_table('booru_artists_temp', 'booru_artists')

    print("Migrating booru_names table")
    create_table('booru_names_temp', **NEW_BOORU_NAMES_TABLE_CONFIG)
    connection.execute(INSERT_BOORU_NAMES)
    drop_table('booru_names')
    op.rename_table('booru_names_temp', 'booru_names')

    print("Creating index")
    create_index('booru_artists', 'ix_booru_artists_artist_id', ['artist_id'], False)


def downgrade_():
    connection = op.get_bind()

    print("Dropping index")
    drop_index('booru_artists', 'ix_booru_artists_artist_id')

    print("Migrating booru_artists table")
    create_table('booru_artists_temp', **OLD_BOORU_ARTISTS_TABLE_CONFIG)
    connection.execute(INSERT_BOORU_ARTISTS)
    drop_table('booru_artists')
    op.rename_table('booru_artists_temp', 'booru_artists')

    print("Migrating booru_names table")
    create_table('booru_names_temp', **OLD_BOORU_NAMES_TABLE_CONFIG)
    connection.execute(INSERT_BOORU_NAMES)
    drop_table('booru_names')
    op.rename_table('booru_names_temp', 'booru_names')

    print("Creating index")
    create_index('booru_artists', 'ix_booru_artists_booru_id', ['booru_id'], False)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

