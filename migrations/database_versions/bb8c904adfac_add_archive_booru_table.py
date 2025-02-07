# MIGRATIONS/VERSIONS/BB8C904ADFAC_ADD_ARCHIVE_BOORU_TABLE.PY
"""Add archive_booru table

Revision ID: bb8c904adfac
Revises: 7ee831bcced3
Create Date: 2025-02-07 11:06:05.687636

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import create_table, drop_table


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'bb8c904adfac'
down_revision = '7ee831bcced3'
branch_labels = None
depends_on = None

ARCHIVE_BOORU_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'archive_id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'danbooru_id',
            'type': 'INTEGER',
            'nullable': True,
        }, {
            'name': 'name',
            'type': 'TEXT',
            'nullable': False,
        }, {
            'name': 'banned',
            'type': 'BOOLEAN',
            'nullable': False,
        }, {
            'name': 'deleted',
            'type': 'BOOLEAN',
            'nullable': False,
        }, {
            'name': 'created',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'updated',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'names',
            'type': 'JSON',
            'nullable': True,
        }, {
            'name': 'notations',
            'type': 'JSON',
            'nullable': True,
        }, {
            'name': 'artists',
            'type': 'JSON',
            'nullable': True,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_archive_booru',
            'columns': ['archive_id'],
        },
    ],
    'fk_config': [
        {
            'name': 'fk_archive_booru_archive_id_archive',
            'columns': ['archive_id'],
            'references': ['archive.id'],
        },
    ],
    'with_rowid': True,
}

ARCHIVE_ARTIST_TABLE_INSERT = """
WITH
archive_booru_body AS (
	SELECT
		archive.id AS archive_id,
		json_extract(archive.data, '$.body.danbooru_id') AS danbooru_id,
		json_extract(archive.data, '$.body.name') AS name,
		json_extract(archive.data, '$.body.banned') AS banned,
		json_extract(archive.data, '$.body.deleted') AS deleted,
		unixepoch(json_extract(archive.data, '$.body.created')) AS created,
		unixepoch(json_extract(archive.data, '$.body.updated')) AS updated
	FROM archive
	JOIN archive_type ON archive_type.id = archive.type_id
	WHERE archive_type.name = 'booru'
),
archive_booru_names AS (
	SELECT
		archive.id AS archive_id,
		json_group_array(names_json.value) AS names
	FROM archive
	JOIN json_each(archive.data, '$.scalars.names') AS names_json
	JOIN archive_type ON archive_type.id = archive.type_id
	WHERE archive_type.name = 'booru'
	GROUP BY archive.id
),
archive_booru_notations AS (
	SELECT
		archive.id AS archive_id,
		json_group_array(
			json_array(
				json_extract(notation_json.value, '$.body'),
				json_extract(notation_json.value, '$.created'),
				json_extract(notation_json.value, '$.updated')
			)
		) AS notations
	FROM archive
	JOIN archive_type ON archive_type.id = archive.type_id
	JOIN json_each(archive.data, '$.attachments.notations') AS notation_json
	WHERE archive_type.name = 'booru'
	GROUP BY archive.id
),
archive_booru_artists AS (
	SELECT 
		archive.id AS archive_id,
		iif(
			booru_arrays.value != '[]',
			json_group_array(json_array(json_extract(booru_arrays.value, '$[0]'), CAST(json_extract(booru_arrays.value, '$[1]') AS INTEGER))),
			NULL
		) AS artists
	FROM archive
	JOIN json_each(replace(replace(replace(replace(json_extract(archive.data, '$.links.artists'), '[', '[['), ']', ']]'), ',', '],['), '-', '","'), '$') AS booru_arrays
	JOIN archive_type ON archive_type.id = archive.type_id
	WHERE archive_type.name = 'booru'
	GROUP BY archive.id
)
INSERT INTO
	archive_booru(
		archive_id,
		danbooru_id,
		name,
		banned,
		deleted,
		created,
		updated,
		names,
		notations,
		artists
	)
SELECT
	archive_booru_body.archive_id,
	archive_booru_body.danbooru_id,
	archive_booru_body.name,
	archive_booru_body.banned,
	archive_booru_body.deleted,
	archive_booru_body.created,
	archive_booru_body.updated,
	archive_booru_names.names,
	archive_booru_notations.notations,
	archive_booru_artists.artists
FROM archive_booru_body
LEFT JOIN archive_booru_names ON archive_booru_names.archive_id = archive_booru_body.archive_id
LEFT JOIN archive_booru_notations ON archive_booru_notations.archive_id = archive_booru_body.archive_id
LEFT JOIN archive_booru_artists ON archive_booru_artists.archive_id = archive_booru_body.archive_id
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    connection = op.get_bind()

    print("Creating archive_booru table")
    create_table('archive_booru', **ARCHIVE_BOORU_TABLE_CONFIG)

    print("Populating archive_artist table")
    connection.execute(ARCHIVE_ARTIST_TABLE_INSERT)


def downgrade_():
    drop_table('archive_booru')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

