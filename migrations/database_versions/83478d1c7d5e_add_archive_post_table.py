# MIGRATIONS/VERSIONS/83478D1C7D5E_ADD_ARCHIVE_POST_TABLE.PY
"""Add archive_post table

Revision ID: 83478d1c7d5e
Revises: b5ec37c7a2f6
Create Date: 2025-02-02 10:50:19.200845

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import create_table, drop_table


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '83478d1c7d5e'
down_revision = 'b5ec37c7a2f6'
branch_labels = None
depends_on = None

ARCHIVE_POST_TABLE_CONFIG = {
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
            'name': 'height',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'width',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'size',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'file_ext',
            'type': 'TEXT',
            'nullable': False,
        }, {
            'name': 'md5',
            'type': 'BLOB',
            'nullable': False,
        }, {
            'name': 'pixel_md5',
            'type': 'BLOB',
            'nullable': True,
        }, {
            'name': 'audio',
            'type': 'BOOLEAN',
            'nullable': True,
        }, {
            'name': 'duration',
            'type': 'REAL',
            'nullable': True,
        }, {
            'name': 'type_id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'created',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'tags',
            'type': 'JSON',
            'nullable': True,
        }, {
            'name': 'notations',
            'type': 'JSON',
            'nullable': True,
        }, {
            'name': 'errors',
            'type': 'JSON',
            'nullable': True,
        }, {
            'name': 'illusts',
            'type': 'JSON',
            'nullable': True,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_archive_post',
            'columns': ['archive_id'],
        },
    ],
    'fk_config': [
        {
            'name': 'fk_archive_post_archive_id_archive',
            'columns': ['archive_id'],
            'references': ['archive.id'],
        }, {
            'name': 'fk_archive_post_type_id_post_type',
            'columns': ['type_id'],
            'references': ['post_type.id'],
        },
    ],
    'with_rowid': True,
}

ARCHIVE_POST_TABLE_INSERT = """
WITH 
archive_post_body AS (
	SELECT
		archive.id AS archive_id,
		json_extract(archive.data, '$.body.width') AS width, 
		json_extract(archive.data, '$.body.height') AS height,
		json_extract(archive.data, '$.body.file_ext') AS file_ext,
		unhex(json_extract(archive.data, '$.body.md5')) AS md5,
		json_extract(archive.data, '$.body.size') AS size,
		json_extract(archive.data, '$.body.danbooru_id') AS danbooru_id,
		unixepoch(json_extract(archive.data, '$.body.created')) AS created,
		post_type.id AS type_id,
		unhex(json_extract(archive.data, '$.body.pixel_md5')) AS pixel_md5,
		json_extract(archive.data, '$.body.duration') AS duration,
		json_extract(archive.data, '$.body.audio') AS audio
	FROM archive
	JOIN archive_type ON archive_type.id = archive.type_id
	JOIN post_type ON post_type.name = json_extract(archive.data, '$.body.type')
	WHERE archive_type.name = 'post'
),
archive_post_errors AS (
	SELECT
		archive.id AS archive_id,
		json_group_array(
			json_array(
				json_extract(error_json.value, '$.module'),
				json_extract(error_json.value, '$.message'),
				json_extract(error_json.value, '$.created')
			)
		) AS errors
	FROM archive
	JOIN archive_type ON archive_type.id = archive.type_id
	JOIN json_each(archive.data, '$.attachments.errors') AS error_json
	WHERE archive_type.name = 'post'
	GROUP BY archive.id
),
archive_post_notations AS (
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
	WHERE archive_type.name = 'post'
	GROUP BY archive.id
),
archive_post_illusts AS (
	SELECT
		archive.id AS archive_id,
		json_group_array(illusts.value) AS illusts
	FROM archive
	JOIN json_each(archive.data, '$.links.illusts') AS illusts
	JOIN archive_type ON archive_type.id = archive.type_id
	WHERE archive_type.name = 'post'
	GROUP BY archive.id
)
INSERT INTO
	archive_post(
		archive_id,
		width, height,
		file_ext,
		md5,
		size,
		danbooru_id,
		created,
		type_id,
		pixel_md5,
		duration,
		audio,
		errors,
		notations,
		illusts
	)
SELECT
	archive_post_body.archive_id,
	archive_post_body.width,
	archive_post_body.height,
	archive_post_body.file_ext,
	archive_post_body.md5,
	archive_post_body.size,
	archive_post_body.danbooru_id,
	archive_post_body.created,
	archive_post_body.type_id,
	archive_post_body.pixel_md5,
	archive_post_body.duration,
	archive_post_body.audio,
	archive_post_errors.errors,
	archive_post_notations.notations,
	archive_post_illusts.illusts
FROM archive_post_body
LEFT JOIN archive_post_errors ON archive_post_errors.archive_id = archive_post_body.archive_id
LEFT JOIN archive_post_notations ON archive_post_notations.archive_id = archive_post_body.archive_id
LEFT JOIN archive_post_illusts ON archive_post_illusts.archive_id = archive_post_body.archive_id;
"""

# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    connection = op.get_bind()

    print("Creating archive_post table")
    create_table('archive_post', **ARCHIVE_POST_TABLE_CONFIG)

    print("Populating archive_post table")
    connection.execute(ARCHIVE_POST_TABLE_INSERT)


def downgrade_():
    drop_table('archive_post')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

