# MIGRATIONS/VERSIONS/7EE831BCCED3_ADD_ARTIST_ARCHIVE_TABLE.PY
"""Add artist_archive table

Revision ID: 7ee831bcced3
Revises: f2cd7a7fb6ab
Create Date: 2025-02-05 13:19:34.327491

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa

# ## PACKAGE IMPORTS
from migrations.tables import create_table, drop_table


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '7ee831bcced3'
down_revision = 'f2cd7a7fb6ab'
branch_labels = None
depends_on = None

ARCHIVE_ARTIST_TABLE_CONFIG = {
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
            'name': 'site_artist_id',
            'type': 'INTEGER',
            'nullable': False,
        }, {
            'name': 'site_created',
            'type': 'INTEGER',
            'nullable': True,
        }, {
            'name': 'site_account',
            'type': 'TEXT',
            'nullable': False,
        }, {
            'name': 'name',
            'type': 'TEXT',
            'nullable': True,
        }, {
            'name': 'profile',
            'type': 'TEXT',
            'nullable': True,
        }, {
            'name': 'active',
            'type': 'BOOLEAN',
            'nullable': False,
        }, {
            'name': 'primary',
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
            'name': 'webpages',
            'type': 'JSON',
            'nullable': True,
        }, {
            'name': 'site_accounts',
            'type': 'JSON',
            'nullable': True,
        }, {
            'name': 'names',
            'type': 'JSON',
            'nullable': True,
        }, {
            'name': 'profiles',
            'type': 'JSON',
            'nullable': True,
        }, {
            'name': 'notations',
            'type': 'JSON',
            'nullable': True,
        }, {
            'name': 'boorus',
            'type': 'JSON',
            'nullable': True,
        },
    ],
    'pk_config': [
        {
            'name': 'pk_archive_artist',
            'columns': ['archive_id'],
        },
    ],
    'fk_config': [
        {
            'name': 'fk_archive_artist_archive_id_archive',
            'columns': ['archive_id'],
            'references': ['archive.id'],
        }, {
            'name': 'fk_archive_artist_site_id_site_descriptor',
            'columns': ['site_id'],
            'references': ['site_descriptor.id'],
        },
    ],
    'with_rowid': True,
}

ARCHIVE_ARTIST_TABLE_INSERT = """
WITH
archive_artist_body AS (
	SELECT
		archive.id AS archive_id,
		site_descriptor.id AS site_id,
		json_extract(archive.data, '$.body.site_artist_id') AS site_artist_id,
		unixepoch(json_extract(archive.data, '$.body.site_created')) AS site_created,
		json_extract(archive.data, '$.body.site_account') AS site_account,
		json_extract(archive.data, '$.body.name') AS name,
		json_extract(archive.data, '$.body.profile') AS profile,
		json_extract(archive.data, '$.body.active') AS active,
		json_extract(archive.data, '$.body.primary') AS "primary",
		unixepoch(json_extract(archive.data, '$.body.created')) AS created,
		unixepoch(json_extract(archive.data, '$.body.updated')) AS updated
	FROM archive
	JOIN archive_type ON archive_type.id = archive.type_id
	JOIN site_descriptor ON site_descriptor.name = json_extract(archive.data, '$.body.site')
	WHERE archive_type.name = 'artist'
),
archive_artist_webpages AS (
	SELECT
		archive.id AS archive_id,
		json_group_array(
			json_array(
				json_extract(webpages_json.value, '$.url'),
				json(json_type(webpages_json.value, '$.active'))
			)
		) AS webpages
	FROM archive
	JOIN archive_type ON archive_type.id = archive.type_id
	JOIN json_each(archive.data, '$.attachments.webpages') AS webpages_json
	WHERE archive_type.name = 'artist'
	GROUP BY archive.id
),
archive_artist_site_accounts AS (
	SELECT
		archive.id AS archive_id,
		json_group_array(site_accounts_json.value) AS site_accounts
	FROM archive
	JOIN json_each(archive.data, '$.scalars.site_accounts') AS site_accounts_json
	JOIN archive_type ON archive_type.id = archive.type_id
	WHERE archive_type.name = 'artist'
	GROUP BY archive.id
),
archive_artist_names AS (
	SELECT
		archive.id AS archive_id,
		json_group_array(names_json.value) AS names
	FROM archive
	JOIN json_each(archive.data, '$.scalars.names') AS names_json
	JOIN archive_type ON archive_type.id = archive.type_id
	WHERE archive_type.name = 'artist'
	GROUP BY archive.id
),
archive_artist_profiles AS (
	SELECT
		archive.id AS archive_id,
		json_group_array(profiles_json.value) AS profiles
	FROM archive
	JOIN json_each(archive.data, '$.scalars.profiles') AS profiles_json
	JOIN archive_type ON archive_type.id = archive.type_id
	WHERE archive_type.name = 'artist'
	GROUP BY archive.id
),
archive_artist_notations AS (
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
	WHERE archive_type.name = 'artist'
	GROUP BY archive.id
),
archive_artist_boorus AS (
	SELECT
		archive.id AS archive_id,
		iif(
			json_extract(archive.data, '$.links.boorus') != '[]',
			json_extract(archive.data, '$.links.boorus'),
			NULL
		) AS boorus
	FROM archive
	JOIN archive_type ON archive_type.id = archive.type_id
	WHERE archive_type.name = 'artist'
)
INSERT INTO
	archive_artist(
		archive_id,
		site_id,
		site_artist_id,
		site_created,
		site_account,
		name,
		profile,
		active,
		"primary",
		created,
		updated,
		webpages,
		site_accounts,
		names,
		profiles,
		notations,
		boorus
	)
SELECT
	archive_artist_body.archive_id,
	archive_artist_body.site_id,
	archive_artist_body.site_artist_id,
	archive_artist_body.site_created,
	archive_artist_body.site_account,
	archive_artist_body.name,
	archive_artist_body.profile,
	archive_artist_body.active,
	archive_artist_body."primary",
	archive_artist_body.created,
	archive_artist_body.updated,
	archive_artist_webpages.webpages,
	archive_artist_site_accounts.site_accounts,
	archive_artist_names.names,
	archive_artist_profiles.profiles,
	archive_artist_notations.notations,
	archive_artist_boorus.boorus
FROM archive_artist_body
LEFT JOIN archive_artist_webpages ON archive_artist_webpages.archive_id = archive_artist_body.archive_id
LEFT JOIN archive_artist_site_accounts ON archive_artist_site_accounts.archive_id = archive_artist_body.archive_id
LEFT JOIN archive_artist_names ON archive_artist_names.archive_id = archive_artist_body.archive_id
LEFT JOIN archive_artist_profiles ON archive_artist_profiles.archive_id = archive_artist_body.archive_id
LEFT JOIN archive_artist_notations ON archive_artist_notations.archive_id = archive_artist_body.archive_id
LEFT JOIN archive_artist_boorus ON archive_artist_boorus.archive_id = archive_artist_body.archive_id
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    connection = op.get_bind()

    print("Creating archive_artist table")
    create_table('archive_artist', **ARCHIVE_ARTIST_TABLE_CONFIG)

    print("Populating archive_artist table")
    connection.execute(ARCHIVE_ARTIST_TABLE_INSERT)


def downgrade_():
    drop_table('archive_artist')


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

