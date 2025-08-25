# MIGRATIONS/VERSIONS/8526A0931166_MIGRATE_ARCHIVE_ILLUST_URLS_FOR_FRAMES.PY
"""Migrate archive_illust urls for frames

Revision ID: 8526a0931166
Revises: b5e978344741
Create Date: 2025-08-24 15:43:24.495033

"""

# ## EXTERNAL IMPORTS
from alembic import op
import sqlalchemy as sa


# ## GLOBAL VARIABLES

# revision identifiers, used by Alembic.
revision = '8526a0931166'
down_revision = 'b5e978344741'
branch_labels = None
depends_on = None

ARCHIVE_ILLUST_TABLE_UPGRADE = """
WITH archive_illust_urls AS (
	SELECT
		archive_illust.archive_id,
		json_group_array(json_array(
			json_extract(illust_urls.value, '$[0]'),
			json_extract(illust_urls.value, '$[1]'),
			json_extract(illust_urls.value, '$[2]'),
			json_extract(illust_urls.value, '$[3]'),
			json_extract(illust_urls.value, '$[4]'),
			json(json_type(illust_urls.value, '$[5]')),
			json_extract(illust_urls.value, '$[6]'),
			NULL
		)) AS urls
	FROM archive_illust
	JOIN json_each(archive_illust.urls, '$') AS illust_urls
	GROUP BY archive_illust.archive_id
)
UPDATE archive_illust
SET urls = archive_illust_urls.urls
FROM archive_illust_urls
WHERE archive_illust_urls.archive_id = archive_illust.archive_id
"""

ARCHIVE_ILLUST_TABLE_DOWNGRADE = """
WITH archive_illust_urls AS (
	SELECT
		archive_illust.archive_id,
		json_group_array(json_array(
			json_extract(illust_urls.value, '$[0]'),
			json_extract(illust_urls.value, '$[1]'),
			json_extract(illust_urls.value, '$[2]'),
			json_extract(illust_urls.value, '$[3]'),
			json_extract(illust_urls.value, '$[4]'),
			json(json_type(illust_urls.value, '$[5]')),
			json_extract(illust_urls.value, '$[6]')
		)) AS urls
	FROM archive_illust
	JOIN json_each(archive_illust.urls, '$') AS illust_urls
	GROUP BY archive_illust.archive_id
)
UPDATE archive_illust
SET urls = archive_illust_urls.urls
FROM archive_illust_urls
WHERE archive_illust_urls.archive_id = archive_illust.archive_id
"""


# ## FUNCTIONS

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


def upgrade_():
    connection = op.get_bind()
    connection.execute(ARCHIVE_ILLUST_TABLE_UPGRADE)


def downgrade_():
    connection = op.get_bind()
    connection.execute(ARCHIVE_ILLUST_TABLE_DOWNGRADE)


def upgrade_jobs():
    pass


def downgrade_jobs():
    pass

