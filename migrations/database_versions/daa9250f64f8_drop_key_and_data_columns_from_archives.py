# MIGRATIONS/VERSIONS/DAA9250F64F8_DROP_KEY_AND_DATA_COLUMNS_FROM_FROM_ARCHIVES.PY
"""Drop key and data columns from archives

Revision ID: daa9250f64f8
Revises: bb8c904adfac
Create Date: 2025-02-07 15:36:32.963139

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations import batch_alter_table
from migrations.columns import add_column, drop_column, alter_column
from migrations.constraints import create_constraint, drop_constraint
from migrations.indexes import create_index, drop_index

# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = 'daa9250f64f8'
down_revision = 'bb8c904adfac'
branch_labels = None
depends_on = None

ARCHIVE_TABLE_PRUNE = """
DELETE FROM archive
WHERE archive.id IN (
	SELECT archive.id
	FROM archive
	JOIN archive_type ON archive_type.id = archive.type_id
	WHERE archive_type.name = 'unknown'
)
"""

ARCHIVE_TABLE_POST_JSON_INSERT = """
WITH
json_post_data AS (
	SELECT
		archive_post.archive_id,
		lower(hex(archive_post.md5)) AS key,
		json_object(
			'body',
			json_object(
				'md5', lower(hex(archive_post.md5)),
				'width', archive_post.width,
				'height', archive_post.height,
				'file_ext', archive_post.file_ext,
				'size', archive_post.size,
				'danbooru_id', archive_post.danbooru_id,
				'created', strftime("%FT%T", archive_post.created, 'unixepoch'),
				'type', post_type.name,
				'pixel_md5',
				iif(
					archive_post.pixel_md5 IS NOT NULL,
					lower(hex(archive_post.pixel_md5)),
					NULL
				),
				'duration', archive_post.duration,
				'audio',
				CASE archive_post.audio
					WHEN 0 THEN json("false")
					WHEN 1 THEN json("true")
				END
			),
			'scalars',
			json_object(),
			'links',
			json_object(
				'illusts',
				json(iif(archive_post.illusts IS NOT NULL, archive_post.illusts, "[]"))
			),
			'attachments',
			json_object(
				'notations',
				iif(
					archive_post.notations IS NOT NULL,
					json_group_array(
						json_object(
							'body', json_extract(notations_array.value, '$[0]'),
							'created', json_extract(notations_array.value, '$[1]'),
							'updated', json_extract(notations_array.value, '$[2]')
						)
					),
					json("[]")
				),
				'errors',
				iif(
					archive_post.errors IS NOT NULL,
					json_group_array(
						json_object(
							'module', json_extract(errors_array.value, '$[0]'),
							'message', json_extract(errors_array.value, '$[1]'),
							'created', json_extract(errors_array.value, '$[2]')
						)
					),
					json("[]")
				)
			)
		) AS data
	FROM archive_post
	JOIN post_type ON post_type.id = archive_post.type_id
	LEFT JOIN json_each(archive_post.notations, '$') AS notations_array
	LEFT JOIN json_each(archive_post.errors, '$') AS errors_array
	GROUP BY archive_post.archive_id
)
UPDATE archive
SET
	key = json_post_data.key,
	data = json_post_data.data
FROM json_post_data
WHERE json_post_data.archive_id = archive.id
"""

ARCHIVE_TABLE_ILLUST_JSON_INSERT = """
WITH
json_illust_data AS (
	SELECT
		archive_illust.archive_id,
		concat(site_descriptor.name, '-', archive_illust.site_illust_id) AS key,
		json_object(
			'body',
			json_object(
				'site', site_descriptor.name,
				'site_illust_id', archive_illust.site_illust_id,
				'site_created', strftime("%FT%T", archive_illust.site_created, 'unixepoch'),
				'title', archive_illust.title,
				'commentary', archive_illust.commentary,
				'pages', archive_illust.pages,
				'score', archive_illust.score,
				'active', iif(archive_illust.active, json("true"), json("false")),
				'created', strftime("%FT%T", archive_illust.created, 'unixepoch'),
				'updated', strftime("%FT%T", archive_illust.created, 'unixepoch')
			),
			'scalars',
			json_object(
				'titles', json(coalesce(archive_illust.titles, "[]")),
				'commentaries', json(coalesce(archive_illust.commentaries, "[]")),
				'additional_commentaries', json(coalesce(archive_illust.additional_commentaries, "[]")),
				'tags', json(coalesce(archive_illust.tags, "[]"))
			),
			'links',
			json_object(
				'artist', archive_illust.site_artist_id
			),
			'attachments',
			json_object(
				'urls',
				iif(
					archive_illust.urls IS NOT NULL,
					json_group_array(
						json_object(
							'order', json_extract(urls_array.value, '$[0]'),
							'url', json_extract(urls_array.value, '$[1]'),
							'sample', json_extract(urls_array.value, '$[2]'),
							'height', json_extract(urls_array.value, '$[3]'),
							'width', json_extract(urls_array.value, '$[4]'),
							'active', json(json_type(urls_array.value, '$[5]')),
							'md5', json_extract(urls_array.value, '$[6]')
						)
					),
					json("[]")
				),
				'notations',
				iif(
					archive_illust.notations IS NOT NULL,
					json_group_array(
						json_object(
							'body', json_extract(notations_array.value, '$[0]'),
							'created', json_extract(notations_array.value, '$[1]'),
							'updated', json_extract(notations_array.value, '$[2]')
						)
					),
					json("[]")
				)
			)
		) AS data
	FROM archive_illust
	JOIN site_descriptor ON site_descriptor.id = archive_illust.site_id
	LEFT JOIN json_each(archive_illust.urls, '$') AS urls_array
	LEFT JOIN json_each(archive_illust.notations, '$') AS notations_array
	GROUP BY archive_illust.archive_id
)
UPDATE archive
SET
	key = json_illust_data.key,
	data = json_illust_data.data
FROM json_illust_data
WHERE json_illust_data.archive_id = archive.id
"""

ARCHIVE_TABLE_ARTIST_JSON_INSERT = """
WITH
json_artist_data AS (
	SELECT
		archive_artist.archive_id,
		concat(site_descriptor.name, '-', archive_artist.site_artist_id) AS key,
		json_object(
			'body',
			json_object(
				'site', site_descriptor.name,
				'site_artist_id', archive_artist.site_artist_id,
				'site_created', strftime("%FT%T", archive_artist.site_created, 'unixepoch'),
				'site_account', archive_artist.site_account,
				'name', archive_artist.name,
				'profile', archive_artist.profile,
				'active', iif(archive_artist.active, json("true"), json("false")),
				'primary', iif(archive_artist.active, json("true"), json("false")),
				'created', strftime("%FT%T", archive_artist.created, 'unixepoch'),
				'updated', strftime("%FT%T", archive_artist.created, 'unixepoch')
			),
			'scalars',
			json_object(
				'site_accounts', json(coalesce(archive_artist.site_accounts, "[]")),
				'names', json(coalesce(archive_artist.names, "[]")),
				'profiles', json(coalesce(archive_artist.profiles, "[]"))
			),
			'links',
			json_object(
				'boorus', json(coalesce(archive_artist.boorus, "[]"))
			),
			'attachments',
			json_object(
				'urls',
				iif(
					archive_artist.webpages IS NOT NULL,
					json_group_array(
						json_object(
							'url', json_extract(webpages_array.value, '$[0]'),
							'active', json(json_type(webpages_array.value, '$[1]'))
						)
					),
					json("[]")
				),
				'notations',
				iif(
					archive_artist.notations IS NOT NULL,
					json_group_array(
						json_object(
							'body', json_extract(notations_array.value, '$[0]'),
							'created', json_extract(notations_array.value, '$[1]'),
							'updated', json_extract(notations_array.value, '$[2]')
						)
					),
					json("[]")
				)
			)
		) AS data
	FROM archive_artist
	JOIN site_descriptor ON site_descriptor.id = archive_artist.site_id
	LEFT JOIN json_each(archive_artist.webpages, '$') AS webpages_array
	LEFT JOIN json_each(archive_artist.notations, '$') AS notations_array
	GROUP BY archive_artist.archive_id
)
UPDATE archive
SET
	key = json_artist_data.key,
	data = json_artist_data.data
FROM json_artist_data
WHERE json_artist_data.archive_id = archive.id
"""

ARCHIVE_TABLE_BOORU_JSON_INSERT = """
WITH
json_booru_data AS (
	SELECT
		archive_booru.archive_id,
		CAST(coalesce(archive_booru.danbooru_id, archive_booru.name) AS TEXT) AS key,
		json_object(
			'body',
			json_object(
				'danbooru_id', archive_booru.danbooru_id,
				'name', archive_booru.name,
				'banned', iif(archive_booru.banned, json("true"), json("false")),
				'deleted', iif(archive_booru.deleted, json("true"), json("false")),
				'created', strftime("%FT%T", archive_booru.created, 'unixepoch'),
				'updated', strftime("%FT%T", archive_booru.created, 'unixepoch')
			),
			'scalars',
			json_object(
				'names', json(coalesce(archive_booru.names, "[]"))
			),
			'links',
			json_object(
				'artists', json(archive_booru.artists)
			),
			'attachments',
			json_object(
				'notations',
				iif(
					archive_booru.notations IS NOT NULL,
					json_group_array(
						json_object(
							'body', json_extract(notations_array.value, '$[0]'),
							'created', json_extract(notations_array.value, '$[1]'),
							'updated', json_extract(notations_array.value, '$[2]')
						)
					),
					json("[]")
				)
			)
		) AS data
	FROM archive_booru
	LEFT JOIN json_each(archive_booru.notations, '$') AS notations_array
	GROUP BY archive_booru.archive_id
)
UPDATE archive
SET
	key = json_booru_data.key,
	data = json_booru_data.data
FROM json_booru_data
WHERE json_booru_data.archive_id = archive.id
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    connection = op.get_bind()

    print("Updating archive table")
    with batch_alter_table('archive', naming=True) as batch_op:
        drop_column(None, 'key', batch_op=batch_op)
        drop_column(None, 'data', batch_op=batch_op)
        drop_constraint(None, 'uq_archive_key_type_id', 'unique', batch_op=batch_op)

    print("Removing unknown entries")
    connection.execute(ARCHIVE_TABLE_PRUNE)

    print("Creating archive indexes")
    create_index('archive_post', 'ix_archive_post_md5', ['md5'], True)
    create_index('archive_illust', 'ix_archive_illust_site_illust_id_site_id', ['site_illust_id', 'site_id'], True)
    create_index('archive_artist', 'ix_archive_artist_site_artist_id_site_id', ['site_artist_id', 'site_id'], True)
    create_index('archive_booru', 'ix_archive_booru_name', ['name'], True)


def downgrade_():
    connection = op.get_bind()

    print("Dropping archive indexes")
    create_index('archive_post', 'ix_archive_post_md5')
    create_index('archive_illust', 'ix_archive_illust_site_illust_id_site_id')
    create_index('archive_artist', 'ix_archive_artist_site_artist_id_site_id')
    create_index('archive_booru', 'ix_archive_booru_name')

    print("Adding columns")
    with batch_alter_table('archive', naming=True) as batch_op:
        add_column(None, 'key', 'TEXT', batch_op=batch_op)
        add_column(None, 'data', 'JSON', batch_op=batch_op)

    print("Populating archive posts")
    connection.execute(ARCHIVE_TABLE_POST_JSON_INSERT)

    print("Populating archive illusts")
    connection.execute(ARCHIVE_TABLE_ILLUST_JSON_INSERT)

    print("Populating archive artists")
    connection.execute(ARCHIVE_TABLE_ARTIST_JSON_INSERT)

    print("Populating archive boorus")
    connection.execute(ARCHIVE_TABLE_BOORU_JSON_INSERT)

    print("Updating archive table")
    with batch_alter_table('archive', naming=True) as batch_op:
        alter_column(None, 'key', 'TEXT', {'nullable': False}, batch_op=batch_op)
        alter_column(None, 'data', 'JSON', {'nullable': False}, batch_op=batch_op)
        create_constraint(None, 'uq_archive_key_type_id', 'unique', (['key', 'type_id'],), batch_op=batch_op)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

