# MIGRATIONS/VERSIONS/F2CD7A7FB6AB_ADD_ARCHIVE_ILLUST_TABLE.PY
"""Add archive_illust table

Revision ID: f2cd7a7fb6ab
Revises: 83478d1c7d5e
Create Date: 2025-02-04 10:30:27.161272

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import create_table, drop_table


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'f2cd7a7fb6ab'
down_revision = '83478d1c7d5e'
branch_labels = None
depends_on = None

ARCHIVE_ILLUST_TABLE_CONFIG = {
    'col_config': [
        {
            'name': 'archive_id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'site_id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'site_illust_id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'site_artist_id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'site_created',
            'type': 'INTEGER',
            'nullable': True,
        }, {
            'name': 'title',
            'type': 'TEXT',
            'nullable': True,
        }, {
            'name': 'commentary',
            'type': 'TEXT',
            'nullable': True,
        }, {
            'name': 'pages',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'score',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'active',
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
            'name': 'urls',
            'type': 'JSON',
            'nullable': True,
        }, {
            'name': 'titles',
            'type': 'JSON',
            'nullable': True,
        }, {
            'name': 'commentaries',
            'type': 'JSON',
            'nullable': True,
        }, {
            'name': 'additional_commentaries',
            'type': 'JSON',
            'nullable': True,
        }, {
            'name': 'tags',
            'type': 'JSON',
            'nullable': True,
        }, {
            'name': 'notations',
            'type': 'JSON',
            'nullable': True,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_archive_illust',
            'columns': ['archive_id'],
        },
    ],
    'fk_config': [
        {
            'name': 'fk_archive_illust_archive_id_archive',
            'columns': ['archive_id'],
            'references': ['archive.id'],
        }, {
            'name': 'fk_archive_illust_site_id_site_descriptor',
            'columns': ['site_id'],
            'references': ['site_descriptor.id'],
        },
    ],
    'with_rowid': True,
}

ARCHIVE_ILLUST_TABLE_INSERT = """
WITH
archive_illust_body AS (
	SELECT
		archive.id AS archive_id,
		site_descriptor.id AS site_id,
		json_extract(archive.data, '$.body.site_illust_id') AS site_illust_id,
		unixepoch(json_extract(archive.data, '$.body.site_created')) AS site_created,
		json_extract(archive.data, '$.links.artist') AS site_artist_id,
		json_extract(archive.data, '$.body.title') AS title,
		json_extract(archive.data, '$.body.commentary') AS commentary,
		json_extract(archive.data, '$.body.pages') AS pages,
		json_extract(archive.data, '$.body.score') AS score,
		json_extract(archive.data, '$.body.active') AS active,
		unixepoch(json_extract(archive.data, '$.body.created')) AS created,
		unixepoch(json_extract(archive.data, '$.body.updated')) AS updated
	FROM archive
	JOIN archive_type ON archive_type.id = archive.type_id
	JOIN site_descriptor ON site_descriptor.name = json_extract(archive.data, '$.body.site')
	WHERE archive_type.name = 'illust'
),
archive_illust_urls AS (
	WITH 
	illust_url_body AS (
		SELECT
			archive.id AS archive_id,
			json_extract(url_json.value, '$.url') AS url,
			json_extract(url_json.value, '$.sample') AS sample,
			json_extract(url_json.value, '$.height') AS height,
			json_extract(url_json.value, '$.width') AS width,
			json_extract(url_json.value, '$.order') AS "order",
			json_type(url_json.value, '$.active') AS active,
			json_extract(url_json.value, '$.key') AS "key"
		FROM archive
		JOIN archive_type ON archive_type.id = archive.type_id
		JOIN json_each(archive.data, '$.attachments.urls') AS url_json
		WHERE archive_type.name = 'illust'
	),
	illust_url_post AS (
		SELECT
			archive.id AS archive_id,
			json_extract(posts_json.value, '$.md5') AS md5,
			json_extract(posts_json.value, '$.key') AS "key"
		FROM archive
		JOIN archive_type ON archive_type.id = archive.type_id
		JOIN json_each(archive.data, '$.links.posts') AS posts_json
		WHERE archive_type.name = 'illust'
	)
	SELECT illust_url_body.archive_id, 
		json_group_array(
			json_array(
				illust_url_body."order",
				illust_url_body.url,
				illust_url_body.sample,
				illust_url_body.height,
				illust_url_body.width,
				json(illust_url_body.active),
				illust_url_post.md5
			)
		) AS urls
	FROM illust_url_body
	LEFT JOIN illust_url_post ON illust_url_post.archive_id = illust_url_body.archive_id AND illust_url_post.key = illust_url_body.key
	GROUP BY illust_url_body.archive_id
),
archive_illust_notations AS (
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
	WHERE archive_type.name = 'illust'
	GROUP BY archive.id
),
archive_illust_tags AS (
	SELECT
		archive.id AS archive_id,
		json_group_array(tags_json.value) AS tags
	FROM archive
	JOIN json_each(archive.data, '$.scalars.tags') AS tags_json
	JOIN archive_type ON archive_type.id = archive.type_id
	WHERE archive_type.name = 'illust'
	GROUP BY archive.id
),
archive_illust_titles AS (
	SELECT
		archive.id AS archive_id,
		json_group_array(titles_json.value) AS titles
	FROM archive
	JOIN json_each(archive.data, '$.scalars.titles') AS titles_json
	JOIN archive_type ON archive_type.id = archive.type_id
	WHERE archive_type.name = 'illust'
	GROUP BY archive.id
),
archive_illust_commentaries AS (
	SELECT
		archive.id AS archive_id,
		json_group_array(commentaries_json.value) AS commentaries
	FROM archive
	JOIN json_each(archive.data, '$.scalars.commentaries') AS commentaries_json
	JOIN archive_type ON archive_type.id = archive.type_id
	WHERE archive_type.name = 'illust'
	GROUP BY archive.id
),
archive_illust_additional_commentaries AS (
	SELECT
		archive.id AS archive_id,
		json_group_array(additional_commentaries_json.value) AS additional_commentaries
	FROM archive
	JOIN json_each(archive.data, '$.scalars.additional_commentaries') AS additional_commentaries_json
	JOIN archive_type ON archive_type.id = archive.type_id
	WHERE archive_type.name = 'illust'
	GROUP BY archive.id
)
INSERT INTO
	archive_illust(
		archive_id,
		site_id,
		site_illust_id,
		site_artist_id,
		site_created,
		title,
		commentary,
		pages,
		score,
		active,
		created,
		updated,
		urls,
		titles,
		commentaries,
		additional_commentaries,
		tags,
		notations
	)
SELECT
	archive_illust_body.archive_id,
	archive_illust_body.site_id,
	archive_illust_body.site_illust_id,
	archive_illust_body.site_artist_id,
	archive_illust_body.site_created,
	archive_illust_body.title,
	archive_illust_body.commentary,
	archive_illust_body.pages,
	archive_illust_body.score,
	archive_illust_body.active,
	archive_illust_body.created,
	archive_illust_body.updated,
	archive_illust_urls.urls,
	archive_illust_titles.titles,
	archive_illust_commentaries.commentaries,
	archive_illust_additional_commentaries.additional_commentaries,
    archive_illust_tags.tags,
    archive_illust_notations.notations
FROM archive_illust_body
LEFT JOIN archive_illust_urls ON archive_illust_urls.archive_id = archive_illust_body.archive_id
LEFT JOIN archive_illust_tags ON archive_illust_tags.archive_id = archive_illust_body.archive_id
LEFT JOIN archive_illust_notations ON archive_illust_notations.archive_id = archive_illust_body.archive_id
LEFT JOIN archive_illust_titles ON archive_illust_titles.archive_id = archive_illust_body.archive_id
LEFT JOIN archive_illust_commentaries ON archive_illust_commentaries.archive_id = archive_illust_body.archive_id
LEFT JOIN archive_illust_additional_commentaries ON archive_illust_additional_commentaries.archive_id = archive_illust_body.archive_id
"""

# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    connection = op.get_bind()

    print("Creating archive_illust table")
    create_table('archive_illust', **ARCHIVE_ILLUST_TABLE_CONFIG)

    print("Populating archive_illust table")
    connection.execute(ARCHIVE_ILLUST_TABLE_INSERT)


def downgrade_():
    drop_table('archive_illust')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

